// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * Plain linear chat transcript for Simple Mode (see SimpleModeView.tsx).
 *
 * <SimpleChartRecBox/> (reused as-is for the input box + live "thinking"
 * status) is built for DataThread's spatial canvas: answers land as
 * `TextTurn`s anchored to a node position in that canvas, and DataThread's
 * own — much larger — rendering logic is what actually draws them as cards
 * on the thread. Simple Mode has no canvas, so this component reads the
 * same `state.textTurns` Redux slice directly and renders it as an ordinary
 * top-to-bottom chat log instead: prompt bubble, then the answer as
 * markdown. `state.textTurns` is a flat array appended to in place (see
 * `addTextTurn` in dfSlice.tsx), so array order already is chronological
 * order — no sorting needed.
 *
 * Known gap: a question answered by *creating a chart* (the agent decided
 * charting fit better than a text explanation) produces no TextTurn, so it
 * won't appear here — this view has no chart canvas to show it on. Direct
 * factual questions overwhelmingly resolve to a text explanation in
 * practice, but it's a real gap, not a hidden one.
 */
import React, { FC, useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import Markdown from 'react-markdown';
import { Box, Typography, Paper } from '@mui/material';

import { DataFormulatorState } from '../app/dfSlice';

export const SimpleConversationHistory: FC = () => {
    const textTurns = useSelector((state: DataFormulatorState) => state.textTurns);
    const bottomRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, [textTurns.length]);

    if (textTurns.length === 0) return null;

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, px: 1, py: 2 }}>
            {textTurns.map((turn) => (
                <Box key={turn.id} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {turn.prompt && (
                        <Paper sx={{
                            alignSelf: 'flex-end', maxWidth: '80%', px: 2, py: 1,
                            backgroundColor: 'primary.main', color: 'primary.contrastText',
                            borderRadius: 2, borderBottomRightRadius: 4,
                        }}>
                            <Typography sx={{ fontSize: '1.05rem', whiteSpace: 'pre-wrap' }}>
                                {turn.prompt}
                            </Typography>
                        </Paper>
                    )}
                    <Paper sx={{
                        alignSelf: 'flex-start', maxWidth: '80%', px: 2, py: 1,
                        backgroundColor: 'background.default', borderRadius: 2, borderBottomLeftRadius: 4,
                        border: '1px solid rgba(255,255,255,0.08)',
                        '& p': { fontSize: '1.05rem', lineHeight: 1.7, m: 0, '&+p': { mt: 1 } },
                        '& ul, & ol': { fontSize: '1.05rem', lineHeight: 1.7, my: 0.5, pl: 3 },
                        '& code': { fontSize: '0.95rem' },
                    }}>
                        <Markdown>{turn.content}</Markdown>
                        {turn.answered && turn.answer && (
                            <Typography sx={{ fontSize: '0.95rem', color: 'text.secondary', mt: 1, fontStyle: 'italic' }}>
                                {turn.answer}
                            </Typography>
                        )}
                    </Paper>
                </Box>
            ))}
            <div ref={bottomRef} />
        </Box>
    );
};
