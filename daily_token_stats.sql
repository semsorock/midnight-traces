-- Query to calculate aggregated statistics for a specific token on a specific date
-- Returns transaction_count, unique_addresses, total_volume
WITH target_asset AS (
    SELECT id 
    FROM multi_asset 
    WHERE fingerprint = 'asset1wd3llgkhsw6etxf2yca6cgk9ssrpva3wf0pq9a' 
),
-- Set your target date here (in UTC)
target_date AS (
    SELECT '2025-12-06'::date AS filter_date
),
daily_txs AS (
    SELECT DISTINCT tx.id
    FROM tx
    JOIN block ON block.id = tx.block_id
    CROSS JOIN target_date
    WHERE block.time AT TIME ZONE 'UTC' >= target_date.filter_date
      AND block.time AT TIME ZONE 'UTC' < target_date.filter_date + INTERVAL '1 day'
),
relevant_outputs AS (
    SELECT 
        tx_out.tx_id,
        tx_out.address,
        ma_tx_out.quantity
    FROM ma_tx_out
    JOIN target_asset ON ma_tx_out.ident = target_asset.id
    JOIN tx_out ON tx_out.id = ma_tx_out.tx_out_id
    JOIN daily_txs ON daily_txs.id = tx_out.tx_id
),
relevant_inputs AS (
    SELECT 
        tx_in.tx_in_id AS tx_id,
        tx_out.address
    FROM tx_in
    JOIN tx_out ON tx_out.tx_id = tx_in.tx_out_id AND tx_out.index = tx_in.tx_out_index
    JOIN ma_tx_out ON ma_tx_out.tx_out_id = tx_out.id
    JOIN target_asset ON ma_tx_out.ident = target_asset.id
    JOIN daily_txs ON daily_txs.id = tx_in.tx_in_id
)
SELECT 
    (SELECT COUNT(DISTINCT id) FROM daily_txs 
     WHERE id IN (SELECT tx_id FROM relevant_outputs) 
        OR id IN (SELECT tx_id FROM relevant_inputs)) AS transaction_count,
        
    (SELECT COUNT(DISTINCT address) FROM (
        SELECT address FROM relevant_outputs
        UNION
        SELECT address FROM relevant_inputs
    ) AS all_addrs) AS unique_addresses,
    
    (SELECT COALESCE(SUM(quantity), 0) FROM relevant_outputs) AS total_volume
;
