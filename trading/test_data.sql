-- ============================================================================
-- Trading Monitor - Comprehensive Test Data
-- ============================================================================
-- Purpose: Generate realistic test data for all 16 scenarios from PRD
-- Usage: PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d root_db -f trading/test_data.sql
-- Note: This script is IDEMPOTENT - can be run multiple times safely
-- ============================================================================

-- Set search path to NocoDB schema
SET search_path TO puqnwnmsw0z9m6s;

-- ============================================================================
-- SECTION 1: CLEANUP - Remove existing test data
-- ============================================================================

BEGIN;

-- Clear all tables and reset auto-increment sequences (CASCADE handles dependencies)
TRUNCATE TABLE position_tracking RESTART IDENTITY CASCADE;
TRUNCATE TABLE order_execution RESTART IDENTITY CASCADE;
TRUNCATE TABLE trade_journal RESTART IDENTITY CASCADE;

-- Delete only test analysis decisions (prefixed with TEST_)
DELETE FROM analysis_decision WHERE "Analysis_Id" LIKE 'TEST_%';

COMMIT;

-- ============================================================================
-- SECTION 2: TEST DATA GENERATION
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- SCENARIO 1: Complete SWING Trade - Profit (Take-Profit Hit)
-- ----------------------------------------------------------------------------
-- Lifecycle: NEW_TRADE → ORDERED → POSITION → CLOSED (TP hit)
-- Expected: Trade closed with profit, exit_reason = 'TARGET_HIT'
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S01_1752287109169',
    '2025-01-10 09:30:00',
    'AAPL:NASDAQ',
    'Analyze AAPL for swing trading opportunity based on daily chart with EMA20, EMA50, EMA200.',
    'AAPL showing bullish breakout above EMA20 ($150.00). Strong support at $145.00, resistance at $160.00. Entry at $150.50, SL $145.00, TP $160.00. R:R ratio 2.1:1.',
    'SWING',
    '{"symbol":"AAPL","analysis_date":"2025-01-10","support":145.00,"resistance":160.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":10,"side":"buy","type":"limit","time_in_force":"day","limit_price":150.50,"stop_loss":{"stop_price":145.00},"take_profit":{"limit_price":160.00},"reward_risk_ratio":2.1,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-10 09:45:00',
    '550e8400-e29b-41d4-a716-446655440001',
    1
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty, exit_date, exit_price, actual_pnl, exit_reason,
    created_at, updated_at
) VALUES (
    'AAPL SWING Trade - Profit',
    'TRADE_S01_001',
    'AAPL',
    'SWING',
    'PATTERN_1',
    'CLOSED',
    'TEST_S01_1752287109169',
    150.50, 145.00, 160.00, 10,
    150.52, 10, '2025-01-15', 160.10, 95.80,
    'TARGET_HIT',
    '2025-01-10 09:45:00',
    '2025-01-15 14:20:00'
);

-- Entry order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S01 Entry Order',
    1, 'TEST_S01_1752287109169', '550e8400-e29b-41d4-a716-446655440001', 'CLIENT_S01_001',
    'ENTRY', 'buy', 'filled', 'day', 10,
    150.50, 10, 150.52, '2025-01-10 10:15:00', '2025-01-10 09:45:00'
);

-- Stop-Loss order (cancelled when TP hit)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S01 Stop-Loss',
    1, 'TEST_S01_1752287109169', '550e8400-e29b-41d4-a716-446655440002',
    'STOP_LOSS', 'sell', 'cancelled', 'gtc', 10,
    145.00, '2025-01-10 10:16:00'
);

-- Take-Profit order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S01 Take-Profit',
    1, 'TEST_S01_1752287109169', '550e8400-e29b-41d4-a716-446655440003',
    'TAKE_PROFIT', 'sell', 'filled', 'gtc', 10,
    160.00, 10, 160.10, '2025-01-15 14:20:00', '2025-01-10 10:16:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 2: Complete SWING Trade - Loss (Stop-Loss Hit)
-- ----------------------------------------------------------------------------
-- Lifecycle: NEW_TRADE → ORDERED → POSITION → CLOSED (SL hit)
-- Expected: Trade closed with loss, exit_reason = 'STOPPED_OUT'
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S02_1752287209169',
    '2025-01-11 09:30:00',
    'NVDA:NASDAQ',
    'Analyze NVDA for swing trading opportunity.',
    'NVDA bouncing from support at $124.00. Entry at $133.80, SL $124.00, TP $145.50. R:R 2.15:1.',
    'SWING',
    '{"symbol":"NVDA","analysis_date":"2025-01-11","support":124.00,"resistance":150.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":5,"side":"buy","type":"limit","time_in_force":"day","limit_price":133.80,"stop_loss":{"stop_price":124.00},"take_profit":{"limit_price":145.50},"reward_risk_ratio":2.15,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-11 09:45:00',
    '550e8400-e29b-41d4-a716-446655440004',
    2
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty, exit_date, exit_price, actual_pnl, exit_reason,
    created_at, updated_at
) VALUES (
    'NVDA SWING Trade - Loss',
    'TRADE_S02_002',
    'NVDA',
    'SWING',
    'PATTERN_1',
    'CLOSED',
    'TEST_S02_1752287209169',
    133.80, 124.00, 145.50, 5,
    133.75, 5, '2025-01-13', 123.90, -49.25,
    'STOPPED_OUT',
    '2025-01-11 09:45:00',
    '2025-01-13 11:30:00'
);

-- Entry order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S02 Entry Order',
    2, 'TEST_S02_1752287209169', '550e8400-e29b-41d4-a716-446655440004', 'CLIENT_S02_002',
    'ENTRY', 'buy', 'filled', 'day', 5,
    133.80, 5, 133.75, '2025-01-11 10:20:00', '2025-01-11 09:45:00'
);

-- Stop-Loss order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S02 Stop-Loss',
    2, 'TEST_S02_1752287209169', '550e8400-e29b-41d4-a716-446655440005',
    'STOP_LOSS', 'sell', 'filled', 'gtc', 5,
    124.00, 5, 123.90, '2025-01-13 11:30:00', '2025-01-11 10:21:00'
);

-- Take-Profit order (cancelled when SL hit)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S02 Take-Profit',
    2, 'TEST_S02_1752287209169', '550e8400-e29b-41d4-a716-446655440006',
    'TAKE_PROFIT', 'sell', 'cancelled', 'gtc', 5,
    145.50, '2025-01-11 10:21:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 3: Complete TREND Trade - Stop-Loss Hit (No TP)
-- ----------------------------------------------------------------------------
-- Lifecycle: NEW_TRADE (TREND) → ORDERED → POSITION → CLOSED (SL hit)
-- Expected: No take-profit order (TREND strategy), closed at SL
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S03_1752287309169',
    '2025-01-12 09:30:00',
    'TSLA:NASDAQ',
    'Analyze TSLA for trend trading opportunity.',
    'TSLA in strong uptrend. Entry at $225.50, trailing SL at $218.00. No fixed TP for trend trade.',
    'TREND',
    '{"symbol":"TSLA","analysis_date":"2025-01-12","support":218.00,"resistance":250.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"TREND","pattern":"PATTERN_3","qty":4,"side":"buy","type":"limit","time_in_force":"day","limit_price":225.50,"stop_loss":{"stop_price":218.00},"reward_risk_ratio":3.5,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-12 09:45:00',
    '550e8400-e29b-41d4-a716-446655440007',
    3
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty, exit_date, exit_price, actual_pnl, exit_reason,
    created_at, updated_at
) VALUES (
    'TSLA TREND Trade - SL Hit',
    'TRADE_S03_003',
    'TSLA',
    'TREND',
    'PATTERN_3',
    'CLOSED',
    'TEST_S03_1752287309169',
    225.50, 218.00, NULL, 4,
    225.45, 4, '2025-01-14', 217.85, -30.40,
    'STOPPED_OUT',
    '2025-01-12 09:45:00',
    '2025-01-14 13:15:00'
);

-- Entry order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S03 Entry Order',
    3, 'TEST_S03_1752287309169', '550e8400-e29b-41d4-a716-446655440007', 'CLIENT_S03_003',
    'ENTRY', 'buy', 'filled', 'day', 4,
    225.50, 4, 225.45, '2025-01-12 10:25:00', '2025-01-12 09:45:00'
);

-- Stop-Loss order (filled) - NO TAKE-PROFIT for TREND trades
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S03 Stop-Loss',
    3, 'TEST_S03_1752287309169', '550e8400-e29b-41d4-a716-446655440008',
    'STOP_LOSS', 'sell', 'filled', 'gtc', 4,
    218.00, 4, 217.85, '2025-01-14 13:15:00', '2025-01-12 10:26:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 4: Partial Fill Scenario
-- ----------------------------------------------------------------------------
-- Lifecycle: NEW_TRADE → ORDERED → POSITION (partial fill)
-- Expected: Position with 5 shares filled (out of 10), SL/TP pending
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S04_1752287409169',
    '2025-01-13 09:30:00',
    'AMD:NASDAQ',
    'Analyze AMD for swing trading opportunity.',
    'AMD consolidating near $140. Entry at $142.00, SL $136.00, TP $152.00.',
    'SWING',
    '{"symbol":"AMD","analysis_date":"2025-01-13","support":136.00,"resistance":152.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_2","qty":10,"side":"buy","type":"limit","time_in_force":"day","limit_price":142.00,"stop_loss":{"stop_price":136.00},"take_profit":{"limit_price":152.00},"reward_risk_ratio":2.5,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-13 09:45:00',
    '550e8400-e29b-41d4-a716-446655440009',
    4
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'AMD SWING Trade - Partial Fill',
    'TRADE_S04_004',
    'AMD',
    'SWING',
    'PATTERN_2',
    'POSITION',
    'TEST_S04_1752287409169',
    142.00, 136.00, 152.00, 10,
    141.98, 5,
    '2025-01-13 09:45:00',
    '2025-01-13 11:00:00'
);

-- Entry order (partially filled - 5 of 10)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S04 Entry Order',
    4, 'TEST_S04_1752287409169', '550e8400-e29b-41d4-a716-446655440009', 'CLIENT_S04_004',
    'ENTRY', 'buy', 'partially_filled', 'day', 10,
    142.00, 5, 141.98, '2025-01-13 11:00:00', '2025-01-13 09:45:00'
);

-- Stop-Loss order (pending, for filled qty only)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S04 Stop-Loss',
    4, 'TEST_S04_1752287409169', '550e8400-e29b-41d4-a716-44665544000a',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 5,
    136.00, '2025-01-13 11:01:00'
);

-- Take-Profit order (pending, for filled qty only)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S04 Take-Profit',
    4, 'TEST_S04_1752287409169', '550e8400-e29b-41d4-a716-44665544000b',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 5,
    152.00, '2025-01-13 11:01:00'
);

-- Active position in position_tracking
INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'AMD Position - Partial',
    4, 'AMD', 5, 141.98,
    143.50, 717.50, 709.90, 7.60,
    '550e8400-e29b-41d4-a716-44665544000a', '550e8400-e29b-41d4-a716-44665544000b',
    '2025-01-13 11:01:00', '2025-01-13 15:00:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 5: Order Cancellation (CANCEL Action)
-- ----------------------------------------------------------------------------
-- Lifecycle: CANCEL decision → Order cancelled → Trade CANCELLED
-- Expected: Order cancelled before fill, trade journal marked CANCELLED
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S05_1752287509169',
    '2025-01-14 09:30:00',
    'MSFT:NASDAQ',
    'Review existing MSFT order for cancellation.',
    'Market conditions changed. Cancel pending MSFT order.',
    'SWING',
    '{"symbol":"MSFT","analysis_date":"2025-01-14","support":385.00,"resistance":410.00,"primary_action":"CANCEL"}'::json,
    true,
    true,
    '2025-01-14 09:45:00',
    '550e8400-e29b-41d4-a716-44665544000c',
    5
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    exit_date, exit_reason,
    created_at, updated_at
) VALUES (
    'MSFT SWING Trade - Cancelled',
    'TRADE_S05_005',
    'MSFT',
    'SWING',
    'PATTERN_1',
    'CANCELLED',
    'TEST_S05_1752287509169',
    395.00, 385.00, 410.00, 3,
    '2025-01-14', 'CANCELLED',
    '2025-01-14 09:00:00',
    '2025-01-14 09:45:00'
);

-- Entry order (cancelled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S05 Entry Order',
    5, 'TEST_S05_1752287509169', '550e8400-e29b-41d4-a716-44665544000c', 'CLIENT_S05_005',
    'ENTRY', 'buy', 'cancelled', 'day', 3,
    395.00, '2025-01-14 09:00:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 6: Order Amendment (AMEND Action)
-- ----------------------------------------------------------------------------
-- Lifecycle: AMEND decision → Old order cancelled → New order placed
-- Expected: Two trade_journal records (old CANCELLED, new ORDERED)
-- ----------------------------------------------------------------------------

-- Original decision (being amended)
INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S06A_1752287609169',
    '2025-01-15 09:30:00',
    'AAPL:NASDAQ',
    'Review and amend existing AAPL order.',
    'AAPL price moved. Amending entry from $151.00 to $148.50.',
    'SWING',
    '{"symbol":"AAPL","analysis_date":"2025-01-15","support":145.00,"resistance":160.00,"primary_action":"AMEND","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":8,"side":"buy","type":"limit","time_in_force":"day","limit_price":148.50,"stop_loss":{"stop_price":143.00},"take_profit":{"limit_price":158.00},"reward_risk_ratio":2.3,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-15 09:45:00',
    '550e8400-e29b-41d4-a716-44665544000d',
    6
);

-- Old trade journal (cancelled)
INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    exit_date, exit_reason,
    created_at, updated_at
) VALUES (
    'AAPL SWING - Old (Amended)',
    'TRADE_S06A_006',
    'AAPL',
    'SWING',
    'PATTERN_1',
    'CANCELLED',
    'TEST_S06A_1752287609169',
    151.00, 145.00, 160.00, 8,
    '2025-01-15', 'AMENDED',
    '2025-01-15 09:00:00',
    '2025-01-15 09:45:00'
);

-- Old entry order (cancelled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S06 Entry Order (Old)',
    6, 'TEST_S06A_1752287609169', '550e8400-e29b-41d4-a716-44665544000d', 'CLIENT_S06A_006',
    'ENTRY', 'buy', 'cancelled', 'day', 8,
    151.00, '2025-01-15 09:00:00'
);

-- New trade journal (ordered with new params)
INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    created_at, updated_at
) VALUES (
    'AAPL SWING - New (After Amend)',
    'TRADE_S06B_007',
    'AAPL',
    'SWING',
    'PATTERN_1',
    'ORDERED',
    'TEST_S06A_1752287609169',
    148.50, 143.00, 158.00, 8,
    '2025-01-15 09:45:00',
    '2025-01-15 09:45:00'
);

-- New entry order (pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S06 Entry Order (New)',
    7, 'TEST_S06A_1752287609169', '550e8400-e29b-41d4-a716-44665544000e', 'CLIENT_S06B_007',
    'ENTRY', 'buy', 'pending', 'day', 8,
    148.50, '2025-01-15 09:45:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 7: NO_ACTION Decision with Existing Position
-- ----------------------------------------------------------------------------
-- Lifecycle: NO_ACTION → days_open incremented, last_review_date updated
-- Expected: Position continues, no new orders
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S07_1752287709169',
    '2025-01-16 09:30:00',
    'NVDA:NASDAQ',
    'Review existing NVDA position.',
    'NVDA position holding well above support. No changes needed.',
    'SWING',
    '{"symbol":"NVDA","analysis_date":"2025-01-16","support":130.00,"resistance":145.00,"primary_action":"NO_ACTION"}'::json,
    true,
    true,
    '2025-01-16 09:45:00',
    NULL,
    8
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty, days_open, last_review_date,
    created_at, updated_at
) VALUES (
    'NVDA SWING - NO_ACTION',
    'TRADE_S07_008',
    'NVDA',
    'SWING',
    'PATTERN_2',
    'POSITION',
    'TEST_S07_1752287709169',
    135.00, 128.00, 148.00, 7,
    135.10, 7, 6, '2025-01-16',
    '2025-01-10 10:00:00',
    '2025-01-16 09:45:00'
);

-- Entry order (filled earlier)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S07 Entry Order',
    8, 'TEST_S07_1752287709169', '550e8400-e29b-41d4-a716-44665544000f', 'CLIENT_S07_008',
    'ENTRY', 'buy', 'filled', 'day', 7,
    135.00, 7, 135.10, '2025-01-10 11:00:00', '2025-01-10 10:00:00'
);

-- Stop-Loss order (pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S07 Stop-Loss',
    8, 'TEST_S07_1752287709169', '550e8400-e29b-41d4-a716-446655440010',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 7,
    128.00, '2025-01-10 11:01:00'
);

-- Take-Profit order (pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S07 Take-Profit',
    8, 'TEST_S07_1752287709169', '550e8400-e29b-41d4-a716-446655440011',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 7,
    148.00, '2025-01-10 11:01:00'
);

-- Active position
INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'NVDA Position - NO_ACTION',
    8, 'NVDA', 7, 135.10,
    138.50, 969.50, 945.70, 23.80,
    '550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440011',
    '2025-01-10 11:01:00', '2025-01-16 15:00:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 8: Position Closed Outside System (Manual Exit)
-- ----------------------------------------------------------------------------
-- Lifecycle: Position closed via Alpaca app → Reconciliation detects
-- Expected: Trade CLOSED, exit_reason = 'MANUAL_EXIT'
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S08_1752287809169',
    '2025-01-17 09:30:00',
    'TSLA:NASDAQ',
    'Analyze TSLA for swing opportunity.',
    'TSLA setup at $230. Entry, SL, TP set.',
    'SWING',
    '{"symbol":"TSLA","analysis_date":"2025-01-17","support":220.00,"resistance":245.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":4,"side":"buy","type":"limit","time_in_force":"day","limit_price":230.00,"stop_loss":{"stop_price":220.00},"take_profit":{"limit_price":245.00},"reward_risk_ratio":2.5,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-17 09:45:00',
    '550e8400-e29b-41d4-a716-446655440012',
    9
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty, exit_date, exit_price, actual_pnl, exit_reason,
    created_at, updated_at
) VALUES (
    'TSLA SWING - Manual Exit',
    'TRADE_S08_009',
    'TSLA',
    'SWING',
    'PATTERN_1',
    'CLOSED',
    'TEST_S08_1752287809169',
    230.00, 220.00, 245.00, 4,
    230.15, 4, '2025-01-18', 235.20, 20.20,
    'MANUAL_EXIT',
    '2025-01-17 09:45:00',
    '2025-01-18 14:30:00'
);

-- Entry order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S08 Entry Order',
    9, 'TEST_S08_1752287809169', '550e8400-e29b-41d4-a716-446655440012', 'CLIENT_S08_009',
    'ENTRY', 'buy', 'filled', 'day', 4,
    230.00, 4, 230.15, '2025-01-17 10:30:00', '2025-01-17 09:45:00'
);

-- Stop-Loss order (cancelled after manual exit)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S08 Stop-Loss',
    9, 'TEST_S08_1752287809169', '550e8400-e29b-41d4-a716-446655440013',
    'STOP_LOSS', 'sell', 'cancelled', 'gtc', 4,
    220.00, '2025-01-17 10:31:00'
);

-- Take-Profit order (cancelled after manual exit)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S08 Take-Profit',
    9, 'TEST_S08_1752287809169', '550e8400-e29b-41d4-a716-446655440014',
    'TAKE_PROFIT', 'sell', 'cancelled', 'gtc', 4,
    245.00, '2025-01-17 10:31:00'
);

-- No position_tracking (already reconciled and removed)

-- ----------------------------------------------------------------------------
-- SCENARIO 9: Pending Orders (Not Yet Filled)
-- ----------------------------------------------------------------------------
-- Lifecycle: NEW_TRADE → Entry order placed but pending
-- Expected: Trade status = ORDERED, order status = pending
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S09_1752287909169',
    '2025-01-18 09:30:00',
    'AMD:NASDAQ',
    'Analyze AMD for swing entry.',
    'AMD limit order at $145.00 waiting for fill.',
    'SWING',
    '{"symbol":"AMD","analysis_date":"2025-01-18","support":140.00,"resistance":155.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":6,"side":"buy","type":"limit","time_in_force":"day","limit_price":145.00,"stop_loss":{"stop_price":140.00},"take_profit":{"limit_price":155.00},"reward_risk_ratio":2.0,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-18 09:45:00',
    '550e8400-e29b-41d4-a716-446655440015',
    10
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    created_at, updated_at
) VALUES (
    'AMD SWING - Pending',
    'TRADE_S09_010',
    'AMD',
    'SWING',
    'PATTERN_1',
    'ORDERED',
    'TEST_S09_1752287909169',
    145.00, 140.00, 155.00, 6,
    '2025-01-18 09:45:00',
    '2025-01-18 09:45:00'
);

-- Entry order (still pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S09 Entry Order',
    10, 'TEST_S09_1752287909169', '550e8400-e29b-41d4-a716-446655440015', 'CLIENT_S09_010',
    'ENTRY', 'buy', 'pending', 'day', 6,
    145.00, '2025-01-18 09:45:00'
);

-- No position yet (order not filled)

-- ----------------------------------------------------------------------------
-- SCENARIO 10: Position with Stale Data (Market Data Unavailable)
-- ----------------------------------------------------------------------------
-- Lifecycle: Active position but old updated_at timestamp
-- Expected: Position exists but last update is old
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S10_1752288009169',
    '2025-01-15 09:30:00',
    'MSFT:NASDAQ',
    'Analyze MSFT for swing opportunity.',
    'MSFT position entered but market data stale.',
    'SWING',
    '{"symbol":"MSFT","analysis_date":"2025-01-15","support":390.00,"resistance":410.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":3,"side":"buy","type":"limit","time_in_force":"day","limit_price":398.00,"stop_loss":{"stop_price":390.00},"take_profit":{"limit_price":410.00},"reward_risk_ratio":2.5,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-15 09:45:00',
    '550e8400-e29b-41d4-a716-446655440016',
    11
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'MSFT SWING - Stale Data',
    'TRADE_S10_011',
    'MSFT',
    'SWING',
    'PATTERN_1',
    'POSITION',
    'TEST_S10_1752288009169',
    398.00, 390.00, 410.00, 3,
    398.20, 3,
    '2025-01-15 09:45:00',
    '2025-01-15 11:00:00'
);

-- Entry order (filled)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S10 Entry Order',
    11, 'TEST_S10_1752288009169', '550e8400-e29b-41d4-a716-446655440016', 'CLIENT_S10_011',
    'ENTRY', 'buy', 'filled', 'day', 3,
    398.00, 3, 398.20, '2025-01-15 11:00:00', '2025-01-15 09:45:00'
);

-- Stop-Loss order (pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S10 Stop-Loss',
    11, 'TEST_S10_1752288009169', '550e8400-e29b-41d4-a716-446655440017',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 3,
    390.00, '2025-01-15 11:01:00'
);

-- Take-Profit order (pending)
INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S10 Take-Profit',
    11, 'TEST_S10_1752288009169', '550e8400-e29b-41d4-a716-446655440018',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 3,
    410.00, '2025-01-15 11:01:00'
);

-- Position with old timestamp (stale data - last updated 3 days ago)
INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'MSFT Position - Stale',
    11, 'MSFT', 3, 398.20,
    399.00, 1197.00, 1194.60, 2.40,
    '550e8400-e29b-41d4-a716-446655440017', '550e8400-e29b-41d4-a716-446655440018',
    '2025-01-15 11:01:00', '2025-01-15 12:00:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 11: Unapproved Decision (Not Executed)
-- ----------------------------------------------------------------------------
-- Lifecycle: Analysis created but not approved
-- Expected: No execution, no orders, no trades
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time
) VALUES (
    'TEST_S11_1752288109169',
    '2025-01-19 09:30:00',
    'AAPL:NASDAQ',
    'Analyze AAPL for potential entry.',
    'AAPL analysis completed but awaiting manual review/approval.',
    'SWING',
    '{"symbol":"AAPL","analysis_date":"2025-01-19","support":148.00,"resistance":162.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":10,"side":"buy","type":"limit","time_in_force":"day","limit_price":155.00,"stop_loss":{"stop_price":148.00},"take_profit":{"limit_price":162.00},"reward_risk_ratio":1.8,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    false,
    false,
    NULL
);

-- No trade_journal, order_execution, or position_tracking records created

-- ----------------------------------------------------------------------------
-- SCENARIO 12: Multiple Positions on Same Symbol
-- ----------------------------------------------------------------------------
-- Lifecycle: Two independent trades on AAPL
-- Expected: Both tracked separately with different trade IDs
-- ----------------------------------------------------------------------------

-- First AAPL position
INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S12A_1752288209169',
    '2025-01-16 09:30:00',
    'AAPL:NASDAQ',
    'AAPL first position - Pattern 1.',
    'AAPL first entry at $152.00.',
    'SWING',
    '{"symbol":"AAPL","analysis_date":"2025-01-16","support":148.00,"resistance":160.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":8,"side":"buy","type":"limit","time_in_force":"day","limit_price":152.00,"stop_loss":{"stop_price":148.00},"take_profit":{"limit_price":160.00},"reward_risk_ratio":2.0,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-16 09:45:00',
    '550e8400-e29b-41d4-a716-446655440019',
    12
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'AAPL SWING #1',
    'TRADE_S12A_012',
    'AAPL',
    'SWING',
    'PATTERN_1',
    'POSITION',
    'TEST_S12A_1752288209169',
    152.00, 148.00, 160.00, 8,
    152.10, 8,
    '2025-01-16 09:45:00',
    '2025-01-16 11:00:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S12A Entry Order',
    12, 'TEST_S12A_1752288209169', '550e8400-e29b-41d4-a716-446655440019', 'CLIENT_S12A_012',
    'ENTRY', 'buy', 'filled', 'day', 8,
    152.00, 8, 152.10, '2025-01-16 11:00:00', '2025-01-16 09:45:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S12A Stop-Loss',
    12, 'TEST_S12A_1752288209169', '550e8400-e29b-41d4-a716-44665544001a',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 8,
    148.00, '2025-01-16 11:01:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S12A Take-Profit',
    12, 'TEST_S12A_1752288209169', '550e8400-e29b-41d4-a716-44665544001b',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 8,
    160.00, '2025-01-16 11:01:00'
);

INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'AAPL Position #1',
    12, 'AAPL', 8, 152.10,
    154.00, 1232.00, 1216.80, 15.20,
    '550e8400-e29b-41d4-a716-44665544001a', '550e8400-e29b-41d4-a716-44665544001b',
    '2025-01-16 11:01:00', '2025-01-18 15:00:00'
);

-- Second AAPL position (different pattern, different entry)
INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S12B_1752288309169',
    '2025-01-17 14:30:00',
    'AAPL:NASDAQ',
    'AAPL second position - Pattern 2.',
    'AAPL second entry at $149.00 (different setup).',
    'SWING',
    '{"symbol":"AAPL","analysis_date":"2025-01-17","support":145.00,"resistance":158.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_2","qty":5,"side":"buy","type":"limit","time_in_force":"day","limit_price":149.00,"stop_loss":{"stop_price":145.00},"take_profit":{"limit_price":158.00},"reward_risk_ratio":2.25,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-17 14:45:00',
    '550e8400-e29b-41d4-a716-44665544001c',
    13
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'AAPL SWING #2',
    'TRADE_S12B_013',
    'AAPL',
    'SWING',
    'PATTERN_2',
    'POSITION',
    'TEST_S12B_1752288309169',
    149.00, 145.00, 158.00, 5,
    148.95, 5,
    '2025-01-17 14:45:00',
    '2025-01-17 15:30:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S12B Entry Order',
    13, 'TEST_S12B_1752288309169', '550e8400-e29b-41d4-a716-44665544001c', 'CLIENT_S12B_013',
    'ENTRY', 'buy', 'filled', 'day', 5,
    149.00, 5, 148.95, '2025-01-17 15:30:00', '2025-01-17 14:45:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S12B Stop-Loss',
    13, 'TEST_S12B_1752288309169', '550e8400-e29b-41d4-a716-44665544001d',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 5,
    145.00, '2025-01-17 15:31:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S12B Take-Profit',
    13, 'TEST_S12B_1752288309169', '550e8400-e29b-41d4-a716-44665544001e',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 5,
    158.00, '2025-01-17 15:31:00'
);

INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'AAPL Position #2',
    13, 'AAPL', 5, 148.95,
    154.00, 770.00, 744.75, 25.25,
    '550e8400-e29b-41d4-a716-44665544001d', '550e8400-e29b-41d4-a716-44665544001e',
    '2025-01-17 15:31:00', '2025-01-18 15:00:00'
);

-- ----------------------------------------------------------------------------
-- SCENARIO 13: Broker Rejection (Order Rejected by Alpaca)
-- ----------------------------------------------------------------------------
-- Lifecycle: Decision executed but order rejected by broker
-- Expected: No trade records, Remarks field shows rejection
-- ----------------------------------------------------------------------------

INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    "Remarks"
) VALUES (
    'TEST_S13_1752288409169',
    '2025-01-19 10:00:00',
    'NVDA:NASDAQ',
    'Analyze NVDA for entry.',
    'NVDA order attempted but rejected by broker due to insufficient buying power.',
    'SWING',
    '{"symbol":"NVDA","analysis_date":"2025-01-19","support":130.00,"resistance":145.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":100,"side":"buy","type":"limit","time_in_force":"day","limit_price":135.00,"stop_loss":{"stop_price":130.00},"take_profit":{"limit_price":145.00},"reward_risk_ratio":2.0,"risk_amount":500.00,"risk_percentage":5.0}}'::json,
    true,
    true,
    '2025-01-19 10:15:00',
    'Order rejected by Alpaca: Insufficient buying power'
);

-- No trade_journal, order_execution, or position_tracking (order rejected before submission)

-- ----------------------------------------------------------------------------
-- SCENARIO 14: Full Lifecycle States (Demonstrating all trade_journal statuses)
-- ----------------------------------------------------------------------------
-- Already covered by scenarios 1-13, but let's verify coverage:
-- - ORDERED: Scenarios 6 (new), 9
-- - POSITION: Scenarios 4, 7, 10, 12 (both)
-- - CLOSED: Scenarios 1, 2, 3, 8
-- - CANCELLED: Scenarios 5, 6 (old)
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- SCENARIO 15: All Primary Actions (NEW_TRADE, CANCEL, AMEND, NO_ACTION)
-- ----------------------------------------------------------------------------
-- Already covered:
-- - NEW_TRADE: Scenarios 1-4, 8-13
-- - CANCEL: Scenario 5
-- - AMEND: Scenario 6
-- - NO_ACTION: Scenario 7
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- SCENARIO 16: Active Positions with Profit and Loss
-- ----------------------------------------------------------------------------
-- Lifecycle: Two active positions, one showing profit, one showing loss
-- Expected: Different unrealized_pnl values
-- ----------------------------------------------------------------------------

-- Position with Profit
INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S16A_1752288509169',
    '2025-01-18 09:30:00',
    'MSFT:NASDAQ',
    'MSFT showing profit.',
    'MSFT position up +$25 unrealized.',
    'SWING',
    '{"symbol":"MSFT","analysis_date":"2025-01-18","support":395.00,"resistance":415.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":2,"side":"buy","type":"limit","time_in_force":"day","limit_price":400.00,"stop_loss":{"stop_price":395.00},"take_profit":{"limit_price":415.00},"reward_risk_ratio":3.0,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-18 09:45:00',
    '550e8400-e29b-41d4-a716-44665544001f',
    14
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'MSFT SWING - Profit',
    'TRADE_S16A_014',
    'MSFT',
    'SWING',
    'PATTERN_1',
    'POSITION',
    'TEST_S16A_1752288509169',
    400.00, 395.00, 415.00, 2,
    400.05, 2,
    '2025-01-18 09:45:00',
    '2025-01-18 11:00:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S16A Entry Order',
    14, 'TEST_S16A_1752288509169', '550e8400-e29b-41d4-a716-44665544001f', 'CLIENT_S16A_014',
    'ENTRY', 'buy', 'filled', 'day', 2,
    400.00, 2, 400.05, '2025-01-18 11:00:00', '2025-01-18 09:45:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S16A Stop-Loss',
    14, 'TEST_S16A_1752288509169', '550e8400-e29b-41d4-a716-446655440020',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 2,
    395.00, '2025-01-18 11:01:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S16A Take-Profit',
    14, 'TEST_S16A_1752288509169', '550e8400-e29b-41d4-a716-446655440021',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 2,
    415.00, '2025-01-18 11:01:00'
);

INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'MSFT Position - Profit',
    14, 'MSFT', 2, 400.05,
    412.50, 825.00, 800.10, 24.90,
    '550e8400-e29b-41d4-a716-446655440020', '550e8400-e29b-41d4-a716-446655440021',
    '2025-01-18 11:01:00', '2025-01-18 15:30:00'
);

-- Position with Loss
INSERT INTO analysis_decision (
    "Analysis_Id", "Date_time", "Ticker", "Analysis_Prompt", "Analysis",
    "Trade_Type", "Decision", "Approve", executed, execution_time,
    existing_order_id, existing_trade_journal_id
) VALUES (
    'TEST_S16B_1752288609169',
    '2025-01-18 10:00:00',
    'TSLA:NASDAQ',
    'TSLA showing loss.',
    'TSLA position down -$18 unrealized.',
    'SWING',
    '{"symbol":"TSLA","analysis_date":"2025-01-18","support":220.00,"resistance":240.00,"primary_action":"NEW_TRADE","new_trade":{"strategy":"SWING","pattern":"PATTERN_1","qty":3,"side":"buy","type":"limit","time_in_force":"day","limit_price":232.00,"stop_loss":{"stop_price":225.00},"take_profit":{"limit_price":242.00},"reward_risk_ratio":1.8,"risk_amount":100.00,"risk_percentage":1.0}}'::json,
    true,
    true,
    '2025-01-18 10:15:00',
    '550e8400-e29b-41d4-a716-446655440022',
    15
);

INSERT INTO trade_journal (
    title, trade_id, symbol, trade_style, pattern, status,
    initial_analysis_id, planned_entry, planned_stop_loss, planned_take_profit, planned_qty,
    actual_entry, actual_qty,
    created_at, updated_at
) VALUES (
    'TSLA SWING - Loss',
    'TRADE_S16B_015',
    'TSLA',
    'SWING',
    'PATTERN_1',
    'POSITION',
    'TEST_S16B_1752288609169',
    232.00, 225.00, 242.00, 3,
    232.10, 3,
    '2025-01-18 10:15:00',
    '2025-01-18 11:30:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id, client_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, filled_qty, filled_avg_price, filled_at, created_at
) VALUES (
    'S16B Entry Order',
    15, 'TEST_S16B_1752288609169', '550e8400-e29b-41d4-a716-446655440022', 'CLIENT_S16B_015',
    'ENTRY', 'buy', 'filled', 'day', 3,
    232.00, 3, 232.10, '2025-01-18 11:30:00', '2025-01-18 10:15:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    stop_price, created_at
) VALUES (
    'S16B Stop-Loss',
    15, 'TEST_S16B_1752288609169', '550e8400-e29b-41d4-a716-446655440023',
    'STOP_LOSS', 'sell', 'pending', 'gtc', 3,
    225.00, '2025-01-18 11:31:00'
);

INSERT INTO order_execution (
    title, trade_journal_id, analysis_decision_id, alpaca_order_id,
    order_type, side, order_status, time_in_force, qty,
    limit_price, created_at
) VALUES (
    'S16B Take-Profit',
    15, 'TEST_S16B_1752288609169', '550e8400-e29b-41d4-a716-446655440024',
    'TAKE_PROFIT', 'sell', 'pending', 'gtc', 3,
    242.00, '2025-01-18 11:31:00'
);

INSERT INTO position_tracking (
    title, trade_journal_id, symbol, qty, avg_entry_price,
    current_price, market_value, cost_basis, unrealized_pnl,
    stop_loss_order_id, take_profit_order_id, created_at, updated_at
) VALUES (
    'TSLA Position - Loss',
    15, 'TSLA', 3, 232.10,
    226.00, 678.00, 696.30, -18.30,
    '550e8400-e29b-41d4-a716-446655440023', '550e8400-e29b-41d4-a716-446655440024',
    '2025-01-18 11:31:00', '2025-01-18 15:30:00'
);

COMMIT;

-- ============================================================================
-- SECTION 3: VERIFICATION QUERIES
-- ============================================================================

-- Summary statistics
SELECT
    'TEST DATA SUMMARY' as info,
    (SELECT COUNT(*) FROM analysis_decision WHERE "Analysis_Id" LIKE 'TEST_%') as total_decisions,
    (SELECT COUNT(*) FROM trade_journal) as total_trades,
    (SELECT COUNT(*) FROM order_execution) as total_orders,
    (SELECT COUNT(*) FROM position_tracking) as active_positions;

-- Trade status breakdown
SELECT
    status,
    COUNT(*) as count
FROM trade_journal
GROUP BY status
ORDER BY status;

-- Position summary
SELECT
    symbol,
    COUNT(*) as position_count,
    SUM(unrealized_pnl) as total_unrealized_pnl
FROM position_tracking
GROUP BY symbol
ORDER BY symbol;

-- ============================================================================
-- END OF TEST DATA SCRIPT
-- ============================================================================
