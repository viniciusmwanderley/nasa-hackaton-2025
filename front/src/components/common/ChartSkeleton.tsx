import React from 'react';
import { Box, Paper, Skeleton } from '@mui/material';

const ChartSkeleton: React.FC = () => {
    return (
        <Paper sx={{ 
            p: 2.5, 
            height: '450px',
            boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
            borderRadius: 2,
            border: '1px solid #f0f0f0'
        }}>
            {/* Título do gráfico */}
            <Skeleton variant="text" width="60%" height={24} sx={{ mb: 2 }} />
            
            {/* Área do gráfico */}
            <Box sx={{ height: 380 }}>
                {/* Eixo Y (skeleton) */}
                <Box sx={{ 
                    display: 'flex', 
                    height: '100%',
                    alignItems: 'flex-end',
                    gap: 1,
                    px: 2,
                    pb: 4
                }}>
                    {[...Array(5)].map((_, index) => (
                        <Box key={index} sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            {/* Barra do gráfico */}
                            <Skeleton 
                                variant="rectangular" 
                                width="80%" 
                                height={`${Math.random() * 60 + 40}%`}
                                sx={{ mb: 1, borderRadius: '4px 4px 0 0' }}
                            />
                            {/* Label do eixo X */}
                            <Skeleton variant="text" width="60%" height={16} />
                        </Box>
                    ))}
                </Box>
            </Box>
        </Paper>
    );
};

const RankingSkeleton: React.FC = () => {
    return (
        <Paper sx={{ 
            p: 3, 
            height: '450px',
            boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
            borderRadius: 2,
            border: '1px solid #f0f0f0'
        }}>
            {/* Título do ranking */}
            <Skeleton variant="text" width="80%" height={20} sx={{ mb: 1, mx: 'auto' }} />
            <Skeleton variant="text" width="70%" height={20} sx={{ mb: 1, mx: 'auto' }} />
            <Skeleton variant="text" width="60%" height={20} sx={{ mb: 3, mx: 'auto' }} />
            
            {/* Items do ranking */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[...Array(5)].map((_, index) => (
                    <Box key={index} sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 2,
                        p: 1
                    }}>
                        {/* Posição */}
                        <Skeleton variant="circular" width={32} height={32} />
                        {/* Nome da cidade */}
                        <Skeleton variant="text" width="50%" height={20} sx={{ flex: 1 }} />
                        {/* Valor */}
                        <Skeleton variant="text" width="30%" height={20} />
                    </Box>
                ))}
            </Box>
        </Paper>
    );
};

export { ChartSkeleton, RankingSkeleton };
