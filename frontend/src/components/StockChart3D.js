import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { Box } from '@mui/material';

const DataPoint = ({ position, height, color, isHighlighted }) => {
  const meshRef = useRef();

  useFrame(() => {
    if (meshRef.current && isHighlighted) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  return (
    <mesh position={position} ref={meshRef}>
      <boxGeometry args={[1, height, 1]} />
      <meshStandardMaterial
        color={color}
        emissive={isHighlighted ? color : '#000000'}
        emissiveIntensity={isHighlighted ? 0.5 : 0}
        roughness={0.3}
        metalness={0.8}
      />
    </mesh>
  );
};

const DataLine = ({ points, color }) => {
  const linePoints = useMemo(() => {
    const pts = [];
    points.forEach(point => {
      pts.push(new THREE.Vector3(point.x, point.y, point.z));
    });
    return pts;
  }, [points]);

  const lineGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry().setFromPoints(linePoints);
    return geometry;
  }, [linePoints]);

  return (
    <line geometry={lineGeometry}>
      <lineBasicMaterial color={color} linewidth={1} />
    </line>
  );
};

const StockChart3D = ({ data = [], width = '100%', height = 400 }) => {
  // Transform the data for 3D visualization
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        points: [],
        linePoints: [],
        maxHeight: 10
      };
    }

    const points = [];
    const linePoints = [];
    let maxValue = Math.max(...data.map(d => d.value));
    let minValue = Math.min(...data.map(d => d.value));

    // Scale factor for better visualization
    const scaleFactor = 10 / (maxValue - minValue || 1);

    data.forEach((point, index) => {
      const normalizedValue = (point.value - minValue) * scaleFactor;
      const x = (index - data.length / 2) * 1.5;
      const y = normalizedValue / 2; // Half height because position is at center
      const z = 0;

      points.push({
        position: [x, y, z],
        height: normalizedValue,
        color: point.value >= 0 ? '#32d794' : '#ff4757',
        isHighlighted: point.isHighlighted
      });

      linePoints.push({ x, y: normalizedValue, z });
    });

    return {
      points,
      linePoints,
      maxHeight: maxValue * scaleFactor
    };
  }, [data]);

  return (
    <Box sx={{ width, height, position: 'relative' }}>
      <Canvas
        camera={{ position: [0, 10, 20], fov: 50 }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} />

        <group position={[0, 0, 0]}>
          {/* Floor grid */}
          <gridHelper
            args={[30, 30, '#1a1a2e', '#27374d']}
            position={[0, -0.1, 0]}
            rotation={[0, 0, 0]}
          />

          {/* Data Points */}
          {chartData.points.map((point, index) => (
            <DataPoint
              key={index}
              position={point.position}
              height={point.height}
              color={point.color}
              isHighlighted={point.isHighlighted}
            />
          ))}

          {/* Line connecting points */}
          <DataLine
            points={chartData.linePoints}
            color="#6562fc"
          />
        </group>

        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          target={[0, chartData.maxHeight / 2, 0]}
        />

        {/* Post-processing effects */}
        <EffectComposer>
          <Bloom
            luminanceThreshold={0.1}
            luminanceSmoothing={0.9}
            intensity={0.4}
          />
        </EffectComposer>
      </Canvas>
    </Box>
  );
};

export default StockChart3D;
