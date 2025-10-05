import type { AppState } from '../types';

export const exportWeatherDataToCSV = (state: AppState): void => {
  const { location, selectedDate, weatherData, forecast, precipitationData, apiData } = state;
  
  if (!weatherData || !apiData) {
    alert('No data available to export. Please load data first.');
    return;
  }

  const csvData: (string | number)[][] = [];
  
  // REPORT HEADER
  csvData.push(['NASA WEATHER DATA REPORT']);
  csvData.push(['Location', `${location.city}, ${location.state}, ${location.country}`]);
  csvData.push(['Coordinates', `${location.latitude}°, ${location.longitude}°`]);
  csvData.push(['Analysis Date', selectedDate]);
  csvData.push(['Report Generated', new Date().toLocaleString('en-US')]);
  csvData.push([]);

  // CURRENT METEOROLOGICAL CONDITIONS
  csvData.push(['CURRENT CONDITIONS']);
  csvData.push(['Parameter', 'Value', 'Unit', 'Classification']);
  
  const getTemperatureClass = (temp: number): string => {
    if (temp > 35) return 'Extreme Heat';
    if (temp > 30) return 'Very Hot';
    if (temp > 25) return 'Hot';
    if (temp > 20) return 'Warm';
    if (temp > 15) return 'Mild';
    if (temp > 10) return 'Cool';
    if (temp > 5) return 'Cold';
    return 'Very Cold';
  };

  const getPrecipitationClass = (chance: number): string => {
    if (chance > 80) return 'Very High Probability';
    if (chance > 60) return 'High Probability';
    if (chance > 40) return 'Moderate Probability';
    if (chance > 20) return 'Low Probability';
    return 'Very Low Probability';
  };

  csvData.push(['Temperature', weatherData.temperature, '°C', getTemperatureClass(weatherData.temperature)]);
  csvData.push(['Precipitation Probability', weatherData.rainChance, '%', getPrecipitationClass(weatherData.rainChance)]);
  csvData.push([]);

  // METEOROLOGICAL RISK ANALYSIS
  if (apiData.classifications) {
    const classifications = apiData.classifications;
    csvData.push(['RISK ANALYSIS']);
    csvData.push(['Risk Factor', 'Percentile/Probability (%)', 'Risk Level', 'Threshold Status']);
    
    const getRiskLevel = (value: number, type: 'percentile' | 'probability'): string => {
      const threshold = type === 'percentile' ? 75 : 70;
      if (value > threshold + 10) return 'Critical';
      if (value > threshold) return 'High';
      if (value > threshold - 25) return 'Moderate';
      return 'Low';
    };

    const getThresholdStatus = (value: number, threshold: number): string => {
      return value > threshold ? 'Above Threshold' : 'Within Normal Range';
    };

    csvData.push(['Extreme Heat', Math.round(classifications.very_hot_temp_percentile || 0), getRiskLevel(classifications.very_hot_temp_percentile || 0, 'percentile'), getThresholdStatus(classifications.very_hot_temp_percentile || 0, 75)]);
    csvData.push(['Precipitation', Math.round(classifications.rain_probability || 0), getRiskLevel(classifications.rain_probability || 0, 'probability'), getThresholdStatus(classifications.rain_probability || 0, 70)]);
    csvData.push(['Strong Winds', Math.round(classifications.very_windy_percentile || 0), getRiskLevel(classifications.very_windy_percentile || 0, 'percentile'), getThresholdStatus(classifications.very_windy_percentile || 0, 75)]);
    csvData.push(['Severe Weather', Math.round(classifications.very_wet_probability || 0), getRiskLevel(classifications.very_wet_probability || 0, 'probability'), getThresholdStatus(classifications.very_wet_probability || 0, 70)]);
    csvData.push(['Snow Conditions', Math.round(classifications.very_snowy_probability || 0), getRiskLevel(classifications.very_snowy_probability || 0, 'probability'), getThresholdStatus(classifications.very_snowy_probability || 0, 70)]);
  }
  csvData.push([]);

  // 7-DAY METEOROLOGICAL FORECAST
  csvData.push(['7-DAY FORECAST ANALYSIS']);
  csvData.push(['Date', 'Weekday', 'Temperature Range (°C)', 'Conditions', 'Temperature Category', 'Selected Period']);
  
  forecast.forEach(day => {
    const date = new Date(day.date);
    const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
    const minTemp = day.minTemperature || 0;
    const maxTemp = day.maxTemperature || 0;
    const avgTemp = (minTemp + maxTemp) / 2;
    
    const getTempCategory = (temp: number): string => {
      if (temp > 30) return 'Hot';
      if (temp > 25) return 'Warm';
      if (temp > 20) return 'Moderate';
      if (temp > 15) return 'Mild';
      if (temp > 10) return 'Cool';
      return 'Cold';
    };
    
    const tempRange = minTemp && maxTemp ? `${minTemp} - ${maxTemp}` : 'N/A';
    const isSelected = day.date === selectedDate ? 'Yes' : 'No';
    
    csvData.push([
      day.date,
      dayName,
      tempRange,
      day.condition?.charAt(0).toUpperCase() + day.condition?.slice(1) || 'Clear',
      getTempCategory(avgTemp),
      isSelected
    ]);
  });
  csvData.push([]);

  // PRECIPITATION ANALYSIS
  csvData.push(['PRECIPITATION FORECAST']);
  csvData.push(['Date', 'Weekday', 'Precipitation (mm)', 'Intensity Classification', 'Weather Impact']);
  
  precipitationData.forEach(precip => {
    const date = new Date(precip.date);
    const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
    
    const getIntensityClass = (value: number): string => {
      if (value > 50) return 'Extreme';
      if (value > 20) return 'Heavy';
      if (value > 10) return 'Moderate';
      if (value > 2.5) return 'Light';
      if (value > 0.1) return 'Trace';
      return 'None';
    };

    const getWeatherImpact = (value: number): string => {
      if (value > 20) return 'Severe Impact';
      if (value > 10) return 'Moderate Impact';
      if (value > 2.5) return 'Minor Impact';
      if (value > 0.1) return 'Minimal Impact';
      return 'No Impact';
    };
    
    csvData.push([
      precip.date,
      dayName,
      precip.value.toFixed(2),
      getIntensityClass(precip.value),
      getWeatherImpact(precip.value)
    ]);
  });
  csvData.push([]);

  // NASA POWER API RAW DATA
  if (apiData.allResults && apiData.allResults.length > 0) {
    csvData.push(['NASA POWER METEOROLOGICAL DATA']);
    csvData.push([
      'Date',
      'Temperature (°C)',
      'Precipitation (mm)',
      'Wind Speed (m/s)',
      'Humidity (%)',
      'Pressure (kPa)',
      'Solar Radiation (MJ/m²)',
      'Min Temp (°C)',
      'Max Temp (°C)'
    ]);
    
    apiData.allResults.forEach(result => {
      csvData.push([
        result.datetime.split('T')[0],
        result.parameters.T2M?.value?.toFixed(1) || 'N/A',
        result.parameters.PRECTOTCORR?.value?.toFixed(2) || 'N/A',
        result.parameters.WS2M?.value?.toFixed(1) || 'N/A',
        result.parameters.RH2M?.value?.toFixed(0) || 'N/A',
        result.parameters.PS?.value?.toFixed(1) || 'N/A',
        result.parameters.ALLSKY_SFC_SW_DWN?.value?.toFixed(1) || 'N/A',
        result.parameters.T2M_MIN?.value?.toFixed(1) || 'N/A',
        result.parameters.T2M_MAX?.value?.toFixed(1) || 'N/A'
      ]);
    });
  }
  csvData.push([]);

  // DATA SOURCE AND METHODOLOGY
  csvData.push(['DATA SOURCE INFORMATION']);
  csvData.push(['Parameter', 'Value']);
  csvData.push(['Data Provider', 'NASA POWER API']);
  csvData.push(['Full Name', 'NASA Prediction of Worldwide Energy Resources']);
  csvData.push(['Spatial Resolution', '0.5° × 0.625°']);
  csvData.push(['Temporal Coverage', '1981 - Present']);
  csvData.push(['Update Frequency', 'Daily']);
  csvData.push(['Data Quality', 'Research Grade']);
  csvData.push(['Website', 'https://power.larc.nasa.gov/']);
  csvData.push([]);
  
  csvData.push(['PARAMETER SPECIFICATIONS']);
  csvData.push(['Parameter', 'NASA Code', 'Description', 'Unit', 'Accuracy']);
  csvData.push(['Temperature', 'T2M', 'Temperature at 2 Meters Above Ground', '°C', '±2°C']);
  csvData.push(['Precipitation', 'PRECTOTCORR', 'Precipitation Corrected Total', 'mm/day', '±15%']);
  csvData.push(['Wind Speed', 'WS2M', 'Wind Speed at 2 Meters', 'm/s', '±1 m/s']);
  csvData.push(['Humidity', 'RH2M', 'Relative Humidity at 2 Meters', '%', '±5%']);
  csvData.push(['Pressure', 'PS', 'Surface Pressure', 'kPa', '±0.5 kPa']);
  csvData.push(['Solar Radiation', 'ALLSKY_SFC_SW_DWN', 'All Sky Surface Shortwave Downward Irradiance', 'MJ/m²/day', '±10%']);

  // Create and download CSV
  const csvContent = csvData.map(row => 
    row.map(field => 
      typeof field === 'string' && (field.includes(',') || field.includes('"')) 
        ? `"${field.replace(/"/g, '""')}"` 
        : field
    ).join(',')
  ).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  link.setAttribute('href', url);
  
  const filename = `nasa_weather_data_${location.city.toLowerCase().replace(/\s+/g, '_')}_${selectedDate}.csv`;
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
