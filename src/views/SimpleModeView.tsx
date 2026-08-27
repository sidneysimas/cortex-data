// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Simple Mode — a standalone, chat-only page for users who don't want (or
 * need) the full chart-building workspace: one big question box, ask in
 * plain language, read the answer.
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
 *
 * Dark theme is a *local* ThemeProvider override (palette.mode: 'dark'),
 * not a change to the app's shared theme — SimpleChartRecBox and everything
 * inside it reads colors from MUI theme tokens (background.paper,
 * text.primary, divider, ...), so it re-skins for free here without any
 * edits to that component. Only the outer frame (heading, page background)
 * is hand-styled below.
 */
import React, { FC, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import { Box, Typography, Link, ThemeProvider, createTheme } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useTranslation } from 'react-i18next';

import { DataFormulatorState, dfSelectors, dfActions } from '../app/dfSlice';
import { SimpleChartRecBox } from './SimpleChartRecBox';
import { SimpleConversationHistory } from './SimpleConversationHistory';
import dfLogo from '../assets/df-logo.png';

const darkTheme = createTheme({
    palette: {
        mode: 'dark',
        background: { default: '#0d1117', paper: '#161b22' },
        primary: { main: '#4f9dff' },
    },
    typography: {
        fontFamily: ["Public Sans", "Helvetica Neue", "Arial", "sans-serif"].join(","),
    },
});

export const SimpleModeView: FC = () => {
    const { t } = useTranslation();
    const dispatch = useDispatch();
    const tables = useSelector(dfSelectors.getAllTables);
    const inputTables = useSelector((state: DataFormulatorState) => state.inputTables);
    const focusedId = useSelector((state: DataFormulatorState) => state.focusedId);
    const activeWorkspace = useSelector((state: DataFormulatorState) => state.activeWorkspace);
    const hasData = !!activeWorkspace && tables.length > 0;

    // The main app auto-focuses a table as soon as it's loaded (DataThread's
    // own mount effect, not present here since this page skips DataThread
    // entirely). Without SOME table focused, SimpleChartRecBox derives an
    // empty `primary_tables` list for every request — confirmed by testing
    // that this alone made the backend return a genuinely empty answer
    // (content_len=0) even though input_tables was populated correctly.
    // Focus the first loaded table once, only if nothing is focused yet —
    // never override a real focus the user (or a resumed session) already set.
    useEffect(() => {
        if (!focusedId && inputTables.length > 0) {
            dispatch(dfActions.setFocused({ type: 'table', tableId: inputTables[0].id }));
        }
    }, [focusedId, inputTables, dispatch]);

    return (
        <ThemeProvider theme={darkTheme}>
            <Box sx={{
                position: 'absolute', inset: 0, overflow: 'auto',
                backgroundColor: 'background.default', display: 'flex', justifyContent: 'center',
            }}>
                <Box sx={{
                    width: '100%', maxWidth: 820, px: 3, py: 5,
                    display: 'flex', flexDirection: 'column', minHeight: '100%',
                }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5, mb: 4 }}>
                        <Box component="img" src={dfLogo} alt="" sx={{ height: 56 }} />
                        <Typography sx={{
                            fontWeight: 600, fontSize: '2rem', color: 'text.primary',
                            letterSpacing: '0.01em', textAlign: 'center',
                        }}>
                            {t('simpleMode.title')}
                        </Typography>
                    </Box>

                    {hasData ? (
                        <Box sx={{
                            flex: 1, backgroundColor: 'background.paper', borderRadius: 3,
                            border: '1px solid rgba(255,255,255,0.08)',
                            boxShadow: '0 4px 24px rgba(0,0,0,0.4)', p: 2,
                            display: 'flex', flexDirection: 'column',
                        }}>
                            <SimpleConversationHistory />
                            <SimpleChartRecBox />
                        </Box>
                    ) : (
                        <Box sx={{
                            display: 'flex', flexDirection: 'column',
                            alignItems: 'center', justifyContent: 'center', textAlign: 'center',
                            backgroundColor: 'background.paper', borderRadius: 3,
                            border: '1px solid rgba(255,255,255,0.08)',
                            boxShadow: '0 4px 24px rgba(0,0,0,0.4)', p: 4, gap: 2, minHeight: 240,
                        }}>
                            <Typography sx={{ fontSize: '1.3rem', color: 'text.primary' }}>
                                {t('simpleMode.noData')}
                            </Typography>
                            <Typography sx={{ fontSize: '1.05rem', color: 'text.secondary' }}>
                                {t('simpleMode.noDataHint')}
                            </Typography>
                        </Box>
                    )}

                    <Link component={RouterLink} to="/app" sx={{
                        display: 'inline-flex', alignItems: 'center', gap: 0.5,
                        mt: 3, fontSize: '1.05rem', color: 'primary.main',
                    }}>
                        <ArrowBackIcon fontSize="small" /> {t('simpleMode.backToFullApp')}
                    </Link>
                </Box>
            </Box>
        </ThemeProvider>
    );
};
