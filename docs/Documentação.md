# WeatherData - Documentação Técnica NASA Hackathon 2025

<div align="center">

![WeatherData Logo](../front/src/assets/painel.png)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![NASA](https://img.shields.io/badge/NASA-E03C31?style=for-the-badge&logo=nasa&logoColor=white)](https://power.larc.nasa.gov/)

</div>

## 📋 Visão Geral do Projeto

WeatherData é uma solução inovadora que fornece análise meteorológica abrangente e avaliação de riscos através de múltiplas aplicações especializadas. Cada aplicação é projetada para lidar com aspectos específicos do processamento e visualização de dados meteorológicos.

### 💻 Visão Geral das Aplicações

#### 1. WeatherData API (apps/api)
- **Objetivo**: Serviço backend principal fornecendo processamento e análise de dados meteorológicos
- **Funcionalidades Principais**:
  - Integração com API NASA POWER
  - Processamento de dados IMERG
  - Cálculos de risco meteorológico
  - Análise de dados históricos
  - Endpoints API RESTful

##### Componentes Principais:
- **Serviço de Clima** (`app/application/weather_service.py`)
  - Processamento de dados meteorológicos em tempo real
  - Cálculos de avaliação de risco
  - Análise de padrões históricos

- **Serviço de Clima e Energia** (`app/application/climate_energy_service.py`)
  - Agregação de dados climáticos
  - Cálculo de métricas de energia
  - Análise de tendências de longo prazo

- **Serviço de Classificação** (`app/application/classification_service.py`)
  - Classificação de padrões meteorológicos
  - Categorização de níveis de risco
  - Alertas meteorológicos automatizados

#### 2. WeatherData Frontend (front/)
- **Objetivo**: Interface do usuário para visualização e interação com dados meteorológicos
- **Funcionalidades Principais**:
  - Mapas meteorológicos interativos
  - Dashboards de visualização de risco
  - Atualizações em tempo real
  - Capacidades de exportação de dados

##### Componentes Principais:
- **Dashboard** (`src/pages/Dashboard/`)
  - Interface principal para monitoramento meteorológico
  - Visualização de dados em tempo real
  - Exibição de avaliação de riscos

- **Painel de Energia** (`src/pages/EnergyPanel/`)
  - Impactos meteorológicos relacionados à energia
  - Previsão de energia renovável
  - Análise de padrões de consumo

- **Cartões de Clima** (`src/components/cards/`)
  - Previsões diárias
  - Indicadores de risco
  - Métricas meteorológicas
  - Gráficos de precipitação

#### 3. Pipeline de Processamento de Dados
- **Objetivo**: Processamento em background e agregação de dados
- **Componentes**:
  - Coletores de dados meteorológicos
  - Workers de cálculo de risco
  - Serviços de agregação de dados
  - Gerenciamento de cache

#### 4. Monitoramento & Análise
- **Objetivo**: Monitoramento de saúde e performance do sistema
- **Componentes**:
  - Métricas Prometheus
  - Dashboards Grafana
  - Stack ELK para logging
  - Gerenciamento de alertas

### Integração do Sistema

Estas aplicações trabalham juntas para fornecer uma solução completa de análise meteorológica:
1. A API processa dados brutos da NASA e fornece endpoints estruturados
2. O Frontend consome esses endpoints e apresenta os dados visualmente
3. Workers em background lidam com tarefas pesadas de processamento
4. O Monitoramento garante a confiabilidade do sistema

WeatherData é desenvolvida durante o NASA Space Apps Challenge 2025. Esta plataforma abrangente utiliza dados de observação terrestre da NASA para fornecer avaliações e previsões precisas de risco meteorológico para atividades ao ar livre. Combinando múltiplas fontes de dados e empregando análises avançadas, entregamos avaliações de risco precisas e específicas para cada localização, ajudando os usuários a tomarem decisões informadas sobre seus planos ao ar livre.

### 🎯 Objetivos Principais

- Fornecer avaliações de risco meteorológico em tempo real para atividades ao ar livre
- Permitir tomada de decisões baseada em dados para planejamento de eventos
- Entregar previsões meteorológicas precisas e específicas por localização
- Monitorar e analisar múltiplas condições climáticas simultaneamente
- Gerar relatórios detalhados de risco e previsões
- Suportar análise de padrões históricos para melhor planejamento

### 🌟 Funcionalidades Principais

#### Avaliação de Risco em Tempo Real
- **Análise Multifatorial**
  - Extremos de temperatura (calor e frio)
  - Probabilidade e intensidade de precipitação
  - Velocidade e direção do vento
  - Índices de umidade e conforto
  - Níveis de radiação UV
  - Métricas de qualidade do ar
  - Combinações personalizadas de fatores de risco

#### Inteligência Meteorológica Avançada
- **Análise de Padrões Históricos**
  - Mais de 20 anos de dados NASA POWER
  - Modelagem estatística para previsão de riscos
  - Identificação de tendências sazonais
  - Avaliação de impacto das mudanças climáticas
  - Reconhecimento de padrões baseado em machine learning

#### Inteligência de Localização
- **Análise Geoespacial Precisa**
  - Integração de dados de satélite de alta resolução
  - Cálculo de risco considerando terreno
  - Consideração de microclima
  - Efeitos de ilha de calor urbana
  - Marcação e monitoramento personalizado de locais

#### Visualização de Dados
- **Mapas Interativos**
  - Camadas de clima em tempo real
  - Mapas de calor de risco
  - Visualização de dados históricos
  - Suporte a marcadores personalizados
  - Padrões climáticos animados
  - Opções de visualização multicamada

#### Personalização e Exportação
- **Configuração de Limites de Risco**
  - Configurações específicas por atividade
  - Limites de alerta personalizados
  - Preferências pessoais de conforto
  - Perfis de risco baseados em tempo
- **Capacidades de Exportação de Dados**
  - Opções de exportação CSV/JSON
  - Suporte à integração via API
  - Relatórios automatizados
  - Templates personalizados de relatório

## 🏗️ Arquitetura Técnica

### Visão Geral do Sistema

A arquitetura do sistema WeatherData segue uma abordagem moderna baseada em microsserviços, utilizando tecnologias cloud-native e melhores práticas para escalabilidade, confiabilidade e manutenibilidade.

#### Componentes do Sistema

```mermaid
graph TD
    subgraph "Camada Frontend"
        A1[Aplicação Web] -->|HTTPS| LB[Balanceador de Carga]
        A2[Web Mobile] -->|HTTPS| LB
    end

    subgraph "Camada API"
        LB -->|HTTP/WebSocket| B[Gateway API/CDN]
        B -->|Requisição/Resposta| C1[Serviço FastAPI 1]
        B -->|Requisição/Resposta| C2[Serviço FastAPI 2]
    end

    subgraph "Processamento de Dados"
        C1 -->|Dados Brutos| D1[API NASA POWER]
        C2 -->|Dados Brutos| D2[API IMERG]
        C1 -->|Cache| E[Cluster Redis]
        C2 -->|Cache| E
        C1 -->|Armazenamento| F[PostgreSQL]
        C2 -->|Armazenamento| F
    end

    subgraph "Processamento em Background"
        G1[Worker Análise Clima] -->|Processamento| E
        G2[Worker Cálculo Risco] -->|Processamento| E
        G3[Worker Agregação Dados] -->|Processamento| F
    end

    subgraph "Monitoramento & Logging"
        H1[Prometheus] -->|Métricas| C1
        H1 -->|Métricas| C2
        H2[ELK Stack] -->|Logs| C1
        H2 -->|Logs| C2
        H3[Dashboards Grafana] -->|Visualização| H1
    end
```

#### Detalhes dos Componentes

1. **Camada Frontend**
   - Aplicação web progressiva em React/TypeScript
   - Design responsivo para mobile e desktop
   - Cache no lado do cliente e capacidades offline
   - Integração WebSocket para atualizações em tempo real

2. **Camada API**
   - Serviços FastAPI com balanceamento de carga
   - Gateway API para roteamento e limitação de requisições
   - Integração CDN para assets estáticos
   - Criptografia SSL/TLS para todos os endpoints

3. **Processamento de Dados**
   - Integração com múltiplas fontes de dados NASA
   - Cache distribuído com Cluster Redis
   - PostgreSQL para armazenamento persistente
   - Versionamento e trilhas de auditoria

4. **Processamento em Background**
   - Processamento assíncrono de tarefas
   - Agregação programada de dados
   - Motor de cálculo de risco
   - Análise de padrões climáticos

5. **Monitoramento & Logging**
   - Métricas do sistema em tempo real
   - Logging centralizado
   - Monitoramento de performance
   - Gerenciamento de alertas

#### Características Principais

- **Alta Disponibilidade**: Sistema projetado para lidar com falhas de componentes de forma elegante
- **Escalabilidade**: Capacidades de escala horizontal para todos os componentes
- **Segurança**: Criptografia ponta a ponta e tratamento seguro de dados
- **Performance**: Otimizado para baixa latência e alto throughput
- **Manutenibilidade**: Design modular com clara separação de responsabilidades

### Arquitetura Backend (Python/FastAPI)

#### Camada de Domínio
- **Entidades Principais**
  ```python
  # app/domain/entities.py
  from datetime import datetime
  from typing import List, Optional
  from pydantic import BaseModel

  class RiscoClima(BaseModel):
      pontuacao_risco: float
      fatores: List[FatorRisco]
      timestamp: datetime
      localizacao: Localizacao
      confianca: float

      def is_risco_alto(self) -> bool:
          return self.pontuacao_risco > 0.7 and self.confianca > 0.8

  class FatorRisco(BaseModel):
      tipo: TipoRisco
      severidade: float
      descricao: str
      recomendacoes: List[str]
  ```

#### Serviços de Aplicação
- **Serviço de Análise Climática**
  ```python
  # app/application/servico_clima.py
  class ServicoClima:
      def __init__(self, 
                   repo_nasa: RepositorioNASA,
                   cache: ServicoCache):
          self._repo_nasa = repo_nasa
          self._cache = cache

      async def analisar_risco_clima(
          self,
          latitude: float,
          longitude: float,
          data: datetime,
          atividades: List[Atividade]
      ) -> RiscoClima:
          chave_cache = f"risco:{latitude}:{longitude}:{data}"
          cached = await self._cache.get(chave_cache)
          if cached:
              return RiscoClima.parse_raw(cached)

          dados_nasa = await self._repo_nasa.obter_dados_clima(
              latitude, longitude, data
          )
          risco = self._calcular_risco(dados_nasa, atividades)
          await self._cache.set(chave_cache, risco.json(), expire=3600)
          return risco
  ```

#### Camada de Infraestrutura
- **Integração com API NASA**
  ```python
  # app/infrastructure/repositorio_nasa.py
  class RepositorioNASA:
      def __init__(self, http_client: HTTPClient):
          self._client = http_client
          self._base_url = "https://power.larc.nasa.gov/api/temporal/"

      async def obter_dados_clima(
          self,
          lat: float,
          lon: float,
          data: datetime
      ) -> DadosClima:
          params = {
              "parameters": "T2M,RH2M,PRECTOT,WS2M",
              "community": "RE",
              "longitude": lon,
              "latitude": lat,
              "start": data.date(),
              "end": data.date(),
              "format": "JSON"
          }
          
          response = await self._client.get(
              f"{self._base_url}daily/point",
              params=params
          )
          
          return self._processar_resposta(response)
  ```

### Arquitetura Frontend (React/TypeScript)

#### Arquitetura de Componentes
- **Componentes Inteligentes**
  ```typescript
  // src/components/CartaoClima/CartaoClima.tsx
  import React from 'react';
  import { useDadosClima } from '@/hooks/useDadosClima';
  import { IconeClima, IndicadorRisco } from '@/components/comum';
  import type { PropsCartaoClima } from '@/types';

  export const CartaoClima: React.FC<PropsCartaoClima> = ({
    latitude,
    longitude,
    data,
    aoAtualizarRisco
  }) => {
    const { data: dados, isLoading, error } = useDadosClima({
      latitude,
      longitude,
      data
    });

    React.useEffect(() => {
      if (dados?.risco) {
        aoAtualizarRisco(dados.risco);
      }
    }, [dados, aoAtualizarRisco]);

    if (isLoading) return <CarregadorSkeleton />;
    if (error) return <EstadoErro error={error} />;

    return (
      <Card className="cartao-clima">
        <header className="cartao-clima__cabecalho">
          <IconeClima condicao={dados.condicao} />
          <BadgeRisco pontuacao={dados.risco.pontuacao} />
        </header>
        <div className="cartao-clima__conteudo">
          <MetricasClima dados={dados.metricas} />
          <FatoresRisco fatores={dados.risco.fatores} />
        </div>
        <footer className="cartao-clima__rodape">
          <TendenciaRisco dados={dados.tendencia} />
          <UltimaAtualizacao data={dados.timestamp} />
        </footer>
      </Card>
    );
  };
  ```

#### Gerenciamento de Estado
- **Integração React Query**
  ```typescript
  // src/hooks/useDadosClima.ts
  import { useQuery } from '@tanstack/react-query';
  import { api } from '@/services/api';
  import type { DadosClima, ParamsClima } from '@/types';

  export const useDadosClima = (params: ParamsClima) => {
    const { latitude, longitude, data } = params;
    
    return useQuery<DadosClima>({
      queryKey: ['clima', latitude, longitude, data],
      queryFn: () => api.getDadosClima(params),
      staleTime: 5 * 60 * 1000, // 5 minutos
      cacheTime: 30 * 60 * 1000, // 30 minutos
      refetchOnWindowFocus: true,
      retry: 2,
    });
  };
  ```

## 🚀 Configuração de Desenvolvimento

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Credenciais da API NASA

### Configuração Backend
```bash
# Clonar repositório
git clone https://github.com/viniciusmwanderley/nasa-hackaton-2025.git
cd nasa-hackaton-2025/apps/api

# Configurar ambiente Python
uv sync
cp .env.example .env

# Configurar variáveis de ambiente
# NASA_API_KEY=sua_chave_api
# DB_CONNECTION=postgresql://usuario:senha@localhost:5432/db
# REDIS_URL=redis://localhost:6379

# Executar migrações
uv run python -m alembic upgrade head

# Executar testes
uv run python -m pytest tests/

# Iniciar servidor de desenvolvimento
uv run dev-server
```

### Configuração Frontend
```bash
cd front
npm install
cp .env.example .env

# Configurar variáveis de ambiente
# VITE_API_BASE_URL=http://localhost:8000

# Iniciar servidor de desenvolvimento
npm run dev
```

## 🧪 Estratégia de Testes

### Testes Backend
- **Testes Unitários**: Lógica de negócio e modelos de domínio
- **Testes de Integração**: Interações com API NASA, operações de banco de dados
- **Testes End-to-End**: Ciclos completos de requisição/resposta
- **Testes de Performance**: Tempos de resposta da API, efetividade do cache
- **Testes de Segurança**: Validação de entrada, autenticação, autorização

### Testes Frontend
- **Testes de Componentes**: Componentes UI individuais
- **Testes de Integração**: Interações entre componentes
- **Testes End-to-End**: Fluxos e cenários de usuário
- **Testes de Regressão Visual**: Consistência da UI
- **Testes de Acessibilidade**: Conformidade WCAG

### Requisitos de Cobertura
- Backend: Mínimo 80% de cobertura
- Frontend: Mínimo 75% de cobertura
- Caminhos críticos: 100% de cobertura

## 📈 Otimização de Performance

### Performance Backend
- Otimização de consultas com índices de banco de dados
- Estratégias eficientes de cache
- Operações assíncronas
- Pool de conexões
- Compressão de respostas

### Performance Frontend
- Code splitting e carregamento lazy
- Otimização de imagens
- Otimização de tamanho de bundle
- Tree shaking
- Implementação de Service Worker

## 🔐 Implementação de Segurança

### Autenticação e Autorização
- Autenticação baseada em JWT
- Controle de acesso baseado em papéis
- Rotação de chaves API
- Gerenciamento de sessão
- Configuração CORS

### Proteção de Dados
- Validação de entrada
- Prevenção contra injeção SQL
- Proteção contra XSS
- Proteção contra CSRF
- Limitação de taxa

## 📊 Monitoramento e Logging

### Monitoramento de Aplicação
- Métricas Prometheus
- Dashboards Grafana
- Rastreamento de erros (Sentry)
- Monitoramento de performance
- Utilização de recursos

### Sistema de Logging
- Logging estruturado
- Agregação de logs
- Rotação de logs
- Relatório de erros
- Logging de auditoria

## 📝 Documentação da API

### Documentação da API
- Swagger UI (/docs)
- ReDoc (/redoc)
- Especificação OpenAPI
- Versionamento da API
- Documentação de limites de taxa

## 🔄 Pipeline CI/CD

### Integração Contínua
- Testes automatizados
- Verificações de qualidade de código
- Varredura de segurança
- Benchmarks de performance

### Implantação Contínua
- Implantação automatizada
- Promoção de ambiente
- Capacidades de rollback
- Flags de feature

## 📄 Licença e Aspectos Legais

### Licenciamento
- Acordo de Código Aberto NASA
- Licenças de terceiros
- Requisitos de atribuição

### Privacidade de Dados
- Conformidade com LGPD
- Políticas de retenção de dados
- Política de privacidade
- Termos de serviço