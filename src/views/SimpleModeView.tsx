// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Simple Mode — a standalone, chat-only page for users who don't want (or
 * can't navigate) the full chart-building workspace: large text, one thing
 * on screen, ask a question in plain language and read the answer.
 *
 * Deliberately NOT nested under <AppShell/> in the router (see App.tsx) —
 * that's what makes the top toolbar, sidebar, and chart canvas absent here
 * without touching any of that shared code. It reuses <SimpleChartRecBox/>
 * as-is for the actual question/answer engine (same tested streaming,
 * clarification, and error handling as the main app) rather than
 * reimplementing that protocol; SimpleChartRecBox already pulls all its data
 * from Redux, so no props need to thread through here. This means: only a
 * browser that already has a workspace open (i.e. someone else loaded data
 * in this same session first) has anything to answer questions about — the
 * empty state below says so plainly instead of showing a confusing blank
 * chat box.
 */
import React, { FC } from 'react';
import { useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Typography, Link } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useTranslation } from 'react-i18next';

import { DataFormulatorState, dfSelectors } from '../app/dfSlice';
import { SimpleChartRecBox } from './SimpleChartRecBox';
import dfLogo from '../assets/df-logo.png';

export const SimpleModeView: FC = () => {
    const { t } = useTranslation();
    const tables = useSelector(dfSelectors.getAllTables);
    const activeWorkspace = useSelector((state: DataFormulatorState) => state.activeWorkspace);
    const hasData = !!activeWorkspace && tables.length > 0;

    return (
        <Box sx={{
            position: 'absolute', inset: 0, overflow: 'auto',
            backgroundColor: '#f5f7fa', display: 'flex', justifyContent: 'center',
        }}>
            <Box sx={{
                width: '100%', maxWidth: 760, px: 3, py: 4,
                display: 'flex', flexDirection: 'column', minHeight: '100%',
            }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 3 }}>
                    <Box component="img" src={dfLogo} alt="" sx={{ height: 40 }} />
                    <Typography variant="h4" sx={{ fontWeight: 500, fontSize: '1.8rem' }}>
                        {t('simpleMode.title')}
                    </Typography>
                </Box>

                {hasData ? (
                    <Box sx={{
                        flex: 1, backgroundColor: 'white', borderRadius: 3,
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)', p: 2,
                        display: 'flex', flexDirection: 'column',
                        '& *': { fontSize: '1.05rem' },
                    }}>
                        <SimpleChartRecBox />
                    </Box>
                ) : (
                    <Box sx={{
                        display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center', textAlign: 'center',
                        backgroundColor: 'white', borderRadius: 3,
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)', p: 4, gap: 2, minHeight: 240,
                    }}>
                        <Typography sx={{ fontSize: '1.3rem', color: 'text.secondary' }}>
                            {t('simpleMode.noData')}
                        </Typography>
                        <Typography sx={{ fontSize: '1.05rem', color: 'text.secondary' }}>
                            {t('simpleMode.noDataHint')}
                        </Typography>
                    </Box>
                )}

                <Link component={RouterLink} to="/app" sx={{
                    display: 'inline-flex', alignItems: 'center', gap: 0.5,
                    mt: 3, fontSize: '1.05rem',
                }}>
                    <ArrowBackIcon fontSize="small" /> {t('simpleMode.backToFullApp')}
                </Link>
            </Box>
        </Box>
    );
};
