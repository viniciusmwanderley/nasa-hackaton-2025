# Outdoor Risk - NASA Hackathon 2025 Technical Documentation

<div align="center">

![Outdoor Risk Logo](../front/src/assets/painel.png)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![NASA](https://img.shields.io/badge/NASA-E03C31?style=for-the-badge&logo=nasa&logoColor=white)](https://power.larc.nasa.gov/)

</div>

## 📋 Project Overview

Outdoor Risk is an innovative solution developed during NASA Space Apps Challenge 2025. This comprehensive platform harnesses NASA's Earth observation data to provide accurate weather risk assessments and predictions for outdoor activities. By combining multiple data sources and employing advanced analytics, we deliver precise, location-specific risk evaluations to help users make informed decisions about their outdoor plans.

### 🎯 Core Objectives

- Deliver real-time weather risk assessments for outdoor activities
- Enable data-driven decision making for event planning
- Provide accurate, location-specific weather predictions
- Monitor and analyze multiple weather conditions simultaneously
- Generate detailed risk reports and forecasts
- Support historical pattern analysis for better planning

### 🌟 Key Features

#### Real-Time Risk Assessment
- **Multi-Factor Analysis**
  - Temperature extremes (heat and cold)
  - Precipitation probability and intensity
  - Wind speed and direction
  - Humidity and comfort indices
  - UV radiation levels
  - Air quality metrics
  - Custom risk factor combinations

#### Advanced Weather Intelligence
- **Historical Pattern Analysis**
  - 20+ years of NASA POWER data
  - Statistical modeling for risk prediction
  - Seasonal trend identification
  - Climate change impact assessment
  - Machine learning-based pattern recognition

#### Location Intelligence
- **Precise Geospatial Analysis**
  - High-resolution satellite data integration
  - Terrain-aware risk calculation
  - Microclimate consideration
  - Urban heat island effects
  - Custom location marking and monitoring

#### Data Visualization
- **Interactive Maps**
  - Real-time weather overlays
  - Risk heat maps
  - Historical data visualization
  - Custom marker support
  - Animated weather patterns
  - Multi-layer visualization options

#### Customization & Export
- **Risk Threshold Configuration**
  - Activity-specific settings
  - Custom alert thresholds
  - Personal comfort preferences
  - Time-based risk profiling
- **Data Export Capabilities**
  - CSV/JSON export options
  - API integration support
  - Automated reporting
  - Custom report templates

## 🏗️ Technical Architecture

### System Overview

The Outdoor Risk system architecture follows a modern microservices-based approach, leveraging cloud-native technologies and best practices for scalability, reliability, and maintainability.

#### System Components

```mermaid
graph TD
    subgraph "Frontend Layer"
        A1[Web Application] -->|HTTPS| LB[Load Balancer]
        A2[Mobile Web] -->|HTTPS| LB
    end

    subgraph "API Layer"
        LB -->|HTTP/WebSocket| B[API Gateway/CDN]
        B -->|Request/Response| C1[FastAPI Service 1]
        B -->|Request/Response| C2[FastAPI Service 2]
    end

    subgraph "Data Processing"
        C1 -->|Raw Data| D1[NASA POWER API]
        C2 -->|Raw Data| D2[IMERG API]
        C1 -->|Cache| E[Redis Cluster]
        C2 -->|Cache| E
        C1 -->|Storage| F[PostgreSQL]
        C2 -->|Storage| F
    end

    subgraph "Background Processing"
        G1[Weather Analysis Worker] -->|Process| E
        G2[Risk Calculation Worker] -->|Process| E
        G3[Data Aggregation Worker] -->|Process| F
    end

    subgraph "Monitoring & Logging"
        H1[Prometheus] -->|Metrics| C1
        H1 -->|Metrics| C2
        H2[ELK Stack] -->|Logs| C1
        H2 -->|Logs| C2
        H3[Grafana Dashboards] -->|Visualization| H1
    end
```

#### Component Details

1. **Frontend Layer**
   - React/TypeScript progressive web application
   - Responsive design for mobile and desktop
   - Client-side caching and offline capabilities
   - WebSocket integration for real-time updates

2. **API Layer**
   - Load-balanced FastAPI services
   - API Gateway for request routing and rate limiting
   - CDN integration for static assets
   - SSL/TLS encryption for all endpoints

3. **Data Processing**
   - Integration with multiple NASA data sources
   - Distributed caching with Redis Cluster
   - PostgreSQL for persistent storage
   - Data versioning and audit trails

4. **Background Processing**
   - Asynchronous task processing
   - Scheduled data aggregation
   - Risk calculation engine
   - Weather pattern analysis

5. **Monitoring & Logging**
   - Real-time system metrics
   - Centralized logging
   - Performance monitoring
   - Alert management

#### Key Characteristics

- **High Availability**: System is designed to handle component failures gracefully
- **Scalability**: Horizontal scaling capabilities for all components
- **Security**: End-to-end encryption and secure data handling
- **Performance**: Optimized for low latency and high throughput
- **Maintainability**: Modular design with clear separation of concerns

### Backend Architecture (Python/FastAPI)

#### Domain Layer
- **Core Entities**
  ```python
  # app/domain/entities.py
  from datetime import datetime
  from typing import List, Optional
  from pydantic import BaseModel

  class WeatherRisk(BaseModel):
      risk_score: float
      factors: List[RiskFactor]
      timestamp: datetime
      location: Location
      confidence: float

      def is_high_risk(self) -> bool:
          return self.risk_score > 0.7 and self.confidence > 0.8

  class RiskFactor(BaseModel):
      type: RiskType
      severity: float
      description: str
      recommendations: List[str]
  ```

#### Application Services
- **Weather Analysis Service**
  ```python
  # app/application/weather_service.py
  class WeatherService:
      def __init__(self, 
                   nasa_repo: NASARepository,
                   cache: CacheService):
          self._nasa_repo = nasa_repo
          self._cache = cache

      async def analyze_weather_risk(
          self,
          latitude: float,
          longitude: float,
          date: datetime,
          activities: List[Activity]
      ) -> WeatherRisk:
          cache_key = f"risk:{latitude}:{longitude}:{date}"
          cached = await self._cache.get(cache_key)
          if cached:
              return WeatherRisk.parse_raw(cached)

          nasa_data = await self._nasa_repo.get_weather_data(
              latitude, longitude, date
          )
          risk = self._calculate_risk(nasa_data, activities)
          await self._cache.set(cache_key, risk.json(), expire=3600)
          return risk
  ```

#### Infrastructure Layer
- **NASA API Integration**
  ```python
  # app/infrastructure/nasa_repository.py
  class NASARepository:
      def __init__(self, http_client: HTTPClient):
          self._client = http_client
          self._base_url = "https://power.larc.nasa.gov/api/temporal/"

      async def get_weather_data(
          self,
          lat: float,
          lon: float,
          date: datetime
      ) -> WeatherData:
          params = {
              "parameters": "T2M,RH2M,PRECTOT,WS2M",
              "community": "RE",
              "longitude": lon,
              "latitude": lat,
              "start": date.date(),
              "end": date.date(),
              "format": "JSON"
          }
          
          response = await self._client.get(
              f"{self._base_url}daily/point",
              params=params
          )
          
          return self._parse_response(response)
  ```

### Frontend Architecture (React/TypeScript)

#### Component Architecture
- **Smart Components**
  ```typescript
  // src/components/WeatherCard/WeatherCard.tsx
  import React from 'react';
  import { useWeatherData } from '@/hooks/useWeatherData';
  import { WeatherIcon, RiskIndicator } from '@/components/common';
  import type { WeatherCardProps } from '@/types';

  export const WeatherCard: React.FC<WeatherCardProps> = ({
    latitude,
    longitude,
    date,
    onRiskUpdate
  }) => {
    const { data, isLoading, error } = useWeatherData({
      latitude,
      longitude,
      date
    });

    React.useEffect(() => {
      if (data?.risk) {
        onRiskUpdate(data.risk);
      }
    }, [data, onRiskUpdate]);

    if (isLoading) return <SkeletonLoader />;
    if (error) return <ErrorState error={error} />;

    return (
      <Card className="weather-card">
        <header className="weather-card__header">
          <WeatherIcon condition={data.condition} />
          <RiskBadge score={data.risk.score} />
        </header>
        <div className="weather-card__content">
          <WeatherMetrics data={data.metrics} />
          <RiskFactors factors={data.risk.factors} />
        </div>
        <footer className="weather-card__footer">
          <RiskTrend data={data.trend} />
          <LastUpdated date={data.timestamp} />
        </footer>
      </Card>
    );
  };
  ```

#### State Management
- **React Query Integration**
  ```typescript
  // src/hooks/useWeatherData.ts
  import { useQuery } from '@tanstack/react-query';
  import { api } from '@/services/api';
  import type { WeatherData, WeatherParams } from '@/types';

  export const useWeatherData = (params: WeatherParams) => {
    const { latitude, longitude, date } = params;
    
    return useQuery<WeatherData>({
      queryKey: ['weather', latitude, longitude, date],
      queryFn: () => api.getWeatherData(params),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      refetchOnWindowFocus: true,
      retry: 2,
    });
  };
  ```

## 🚀 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- NASA API credentials

### Backend Setup
```bash
# Clone repository
git clone https://github.com/viniciusmwanderley/nasa-hackaton-2025.git
cd nasa-hackaton-2025/apps/api

# Set up Python environment
uv sync
cp .env.example .env

# Configure environment variables
# NASA_API_KEY=your_api_key
# DB_CONNECTION=postgresql://user:pass@localhost:5432/db
# REDIS_URL=redis://localhost:6379

# Run migrations
uv run python -m alembic upgrade head

# Run tests
uv run python -m pytest tests/

# Start development server
uv run dev-server
```

### Frontend Setup
```bash
cd front
npm install
cp .env.example .env

# Configure environment variables
# VITE_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev
```

## 🧪 Testing Strategy

### Backend Testing
- **Unit Tests**: Core business logic and domain models
- **Integration Tests**: NASA API interactions, database operations
- **End-to-End Tests**: Complete request/response cycles
- **Performance Tests**: API response times, caching effectiveness
- **Security Tests**: Input validation, authentication, authorization

### Frontend Testing
- **Component Tests**: Individual UI components
- **Integration Tests**: Component interactions
- **End-to-End Tests**: User flows and scenarios
- **Visual Regression Tests**: UI consistency
- **Accessibility Tests**: WCAG compliance

### Test Coverage Requirements
- Backend: Minimum 80% coverage
- Frontend: Minimum 75% coverage
- Critical paths: 100% coverage

## 📈 Performance Optimization

### Backend Performance
- Query optimization with database indexes
- Efficient caching strategies
- Asynchronous operations
- Connection pooling
- Response compression

### Frontend Performance
- Code splitting and lazy loading
- Image optimization
- Bundle size optimization
- Tree shaking
- Service Worker implementation

## 🔐 Security Implementation

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- API key rotation
- Session management
- CORS configuration

### Data Protection
- Input validation
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting

## 📊 Monitoring & Logging

### Application Monitoring
- Prometheus metrics
- Grafana dashboards
- Error tracking (Sentry)
- Performance monitoring
- Resource utilization

### Logging System
- Structured logging
- Log aggregation
- Log rotation
- Error reporting
- Audit logging

## 📝 API Documentation

### API Documentation
- Swagger UI (/docs)
- ReDoc (/redoc)
- OpenAPI specification
- API versioning
- Rate limiting documentation

## 🔄 CI/CD Pipeline

### Continuous Integration
- Automated testing
- Code quality checks
- Security scanning
- Performance benchmarking

### Continuous Deployment
- Automated deployment
- Environment promotion
- Rollback capabilities
- Feature flags

## 📄 License & Legal

### Licensing
- NASA Open Source Agreement
- Third-party licenses
- Attribution requirements

### Data Privacy
- GDPR compliance
- Data retention policies
- Privacy policy
- Terms of service