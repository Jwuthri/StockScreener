import React from 'react';
import { Box, Typography, Tabs, Tab, Grid, TextField, Slider, ToggleButtonGroup, ToggleButton, FormControl, InputLabel, Select, MenuItem, Switch } from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';

const AdvancedFilters = ({
  showAdvanced,
  setShowAdvanced,
  selectedFilterTab,
  handleFilterTabChange,
  priceFilterType,
  handlePriceFilterTypeChange,
  priceRange,
  handlePriceRangeChange,
  priceAbove,
  setPriceAbove,
  priceBelow,
  setPriceBelow,
  changeFilterType,
  handleChangeFilterTypeChange,
  changeRange,
  handleChangeRangeChange,
  changeMin,
  setChangeMin,
  changeMax,
  setChangeMax,
  volumeRange,
  handleVolumeRangeChange,
  handleVolumeInputChange,
  sector,
  handleSectorChange,
  sectors,
  industry,
  handleIndustryChange,
  industries,
  exchange,
  handleExchangeChange,
  exchanges,
  formatPrice,
  formatPercentage,
  formatVolume
}) => {
  return (
    <>
      <Box sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        p: 2,
        backgroundColor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
        borderRadius: 2,
        mb: 2,
        mt: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
          <Typography variant="subtitle1" fontWeight={500}>
            Advanced Filters
          </Typography>
        </Box>
        <Switch
          checked={showAdvanced}
          onChange={(e) => setShowAdvanced(e.target.checked)}
          color="primary"
        />
      </Box>

      {showAdvanced && (
        <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
          <Typography variant="subtitle1" gutterBottom>
            Narrow down stocks:
          </Typography>

          <Tabs
            value={selectedFilterTab}
            onChange={handleFilterTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="standard"
            sx={{ mb: 2 }}
          >
            <Tab label="Price" value="price" />
            <Tab label="Change %" value="change" />
            <Tab label="Volume" value="volume" />
            <Tab label="Sector" value="sector" />
          </Tabs>

          {selectedFilterTab === "price" && (
            <Box>
              <Box sx={{ mb: 3 }}>
                <ToggleButtonGroup
                  value={priceFilterType}
                  exclusive
                  onChange={handlePriceFilterTypeChange}
                  fullWidth
                  color="primary"
                  sx={{ mb: 2 }}
                >
                  <ToggleButton value="range">Price Range</ToggleButton>
                  <ToggleButton value="above">Above Price</ToggleButton>
                  <ToggleButton value="below">Below Price</ToggleButton>
                </ToggleButtonGroup>

                {priceFilterType === "range" && (
                  <>
                    <Typography gutterBottom>
                      Price Range: ${priceRange[0]} to ${priceRange[1]}
                    </Typography>
                    <Slider
                      value={priceRange}
                      onChange={handlePriceRangeChange}
                      valueLabelDisplay="auto"
                      valueLabelFormat={formatPrice}
                      min={0}
                      max={2000}
                      sx={{ mt: 1 }}
                    />
                  </>
                )}

                {priceFilterType === "above" && (
                  <TextField
                    label="Price Above"
                    type="number"
                    value={priceAbove}
                    onChange={(e) => setPriceAbove(Number(e.target.value))}
                    fullWidth
                    InputProps={{
                      startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                      inputProps: { min: 0 }
                    }}
                  />
                )}

                {priceFilterType === "below" && (
                  <TextField
                    label="Price Below"
                    type="number"
                    value={priceBelow}
                    onChange={(e) => setPriceBelow(Number(e.target.value))}
                    fullWidth
                    InputProps={{
                      startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                      inputProps: { min: 0 }
                    }}
                  />
                )}
              </Box>
            </Box>
          )}

          {selectedFilterTab === "change" && (
            <Box>
              <Box sx={{ mb: 3 }}>
                <ToggleButtonGroup
                  value={changeFilterType}
                  exclusive
                  onChange={handleChangeFilterTypeChange}
                  fullWidth
                  color="primary"
                  sx={{ mb: 2 }}
                >
                  <ToggleButton value="any">Any Change Range</ToggleButton>
                  <ToggleButton value="up">% Up Only</ToggleButton>
                  <ToggleButton value="down">% Down Only</ToggleButton>
                </ToggleButtonGroup>

                {changeFilterType === "any" && (
                  <>
                    <Typography gutterBottom>
                      Change %: {changeRange[0]}% to {changeRange[1]}%
                    </Typography>
                    <Slider
                      value={changeRange}
                      onChange={handleChangeRangeChange}
                      valueLabelDisplay="auto"
                      valueLabelFormat={formatPercentage}
                      min={-200}
                      max={200}
                      sx={{ mt: 1 }}
                    />
                  </>
                )}

                {changeFilterType === "up" && (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="Minimum % Change"
                        type="number"
                        value={changeMin}
                        onChange={(e) => setChangeMin(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          endAdornment: <Typography>%</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Maximum % Change"
                        type="number"
                        value={changeMax}
                        onChange={(e) => setChangeMax(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          endAdornment: <Typography>%</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                  </Grid>
                )}

                {changeFilterType === "down" && (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="Minimum % Down"
                        type="number"
                        value={changeMin}
                        onChange={(e) => setChangeMin(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          endAdornment: <Typography>%</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Maximum % Down"
                        type="number"
                        value={changeMax}
                        onChange={(e) => setChangeMax(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          endAdornment: <Typography>%</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                  </Grid>
                )}
              </Box>
            </Box>
          )}

          {selectedFilterTab === "volume" && (
            <Box>
              <Typography gutterBottom>
                Volume Range: {formatVolume(volumeRange[0])} to {formatVolume(volumeRange[1])}
              </Typography>
              <Slider
                value={volumeRange}
                onChange={handleVolumeRangeChange}
                valueLabelDisplay="auto"
                valueLabelFormat={formatVolume}
                min={1000}
                max={100000000}
                step={10000}
                scale={(x) => x}
              />

              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={6}>
                  <TextField
                    label="Min Volume"
                    type="number"
                    value={volumeRange[0]}
                    onChange={(e) => handleVolumeInputChange(0, e)}
                    fullWidth
                    InputProps={{
                      inputProps: { min: 0 }
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Max Volume"
                    type="number"
                    value={volumeRange[1]}
                    onChange={(e) => handleVolumeInputChange(1, e)}
                    fullWidth
                    InputProps={{
                      inputProps: { min: 0 }
                    }}
                  />
                </Grid>
              </Grid>
            </Box>
          )}

          {selectedFilterTab === "sector" && (
            <Box sx={{ p: 1 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Sector</InputLabel>
                    <Select
                      value={sector}
                      onChange={handleSectorChange}
                      label="Sector"
                    >
                      <MenuItem value="">
                        <em>All Sectors</em>
                      </MenuItem>
                      {sectors.map((sector) => (
                        <MenuItem key={sector} value={sector}>{sector}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Industry</InputLabel>
                    <Select
                      value={industry}
                      onChange={handleIndustryChange}
                      label="Industry"
                    >
                      <MenuItem value="">
                        <em>All Industries</em>
                      </MenuItem>
                      {industries.map((ind) => (
                        <MenuItem key={ind} value={ind}>{ind}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={12} sx={{ mt: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel>Exchange</InputLabel>
                    <Select
                      value={exchange}
                      onChange={handleExchangeChange}
                      label="Exchange"
                    >
                      <MenuItem value="">
                        <em>All Exchanges</em>
                      </MenuItem>
                      {exchanges.map((ex) => (
                        <MenuItem key={ex} value={ex}>{ex}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      )}
    </>
  );
};

export default AdvancedFilters;
