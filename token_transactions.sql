-- Query to select transactions involving a specific token fingerprint for a specific date (UTC)
-- Returns tx_hash, input_utxos (filtering for the token), and output_utxos (filtering for the token)

WITH target_asset AS (
    SELECT id 
    FROM multi_asset 
    WHERE fingerprint = 'asset1wd3llgkhsw6etxf2yca6cgk9ssrpva3wf0pq9a' 
),
-- Set your target date here (in UTC)
target_date AS (
    SELECT '2025-12-06'::date AS filter_date
),
relevant_tx_ids AS (
    SELECT DISTINCT involved_txs.tx_id
    FROM (
        -- Transactions where the token is in an output
        SELECT tx_out.tx_id
        FROM ma_tx_out
        JOIN tx_out ON tx_out.id = ma_tx_out.tx_out_id
        JOIN target_asset ON ma_tx_out.ident = target_asset.id
        
        UNION ALL
        
        -- Transactions where the token is in an input (spent)
        SELECT tx_in.tx_in_id AS tx_id
        FROM tx_in
        JOIN tx_out ON tx_out.tx_id = tx_in.tx_out_id AND tx_out.index = tx_in.tx_out_index
        JOIN ma_tx_out ON ma_tx_out.tx_out_id = tx_out.id
        JOIN target_asset ON ma_tx_out.ident = target_asset.id
    ) AS involved_txs
    -- Join with tx and block to filter by date
    JOIN tx ON tx.id = involved_txs.tx_id
    JOIN block ON block.id = tx.block_id
    CROSS JOIN target_date
    WHERE block.time AT TIME ZONE 'UTC' >= target_date.filter_date
      AND block.time AT TIME ZONE 'UTC' < target_date.filter_date + INTERVAL '1 day'
    ORDER BY involved_txs.tx_id DESC
),
-- Fetch input UTXOs containing the token for these transactions
relevant_inputs AS (
    SELECT 
        tx_in.tx_in_id AS tx_id,
        jsonb_build_object(
            'tx_hash', encode(source_tx.hash, 'hex'),
            'tx_index', tx_in.tx_out_index,
            'address', source_tx_out.address,
            'quantity', ma_tx_out.quantity
        ) AS utxo_info
    FROM relevant_tx_ids
    JOIN tx_in ON tx_in.tx_in_id = relevant_tx_ids.tx_id
    JOIN tx_out source_tx_out ON source_tx_out.tx_id = tx_in.tx_out_id AND source_tx_out.index = tx_in.tx_out_index
    JOIN tx source_tx ON source_tx.id = source_tx_out.tx_id
    JOIN ma_tx_out ON ma_tx_out.tx_out_id = source_tx_out.id
    JOIN target_asset ON ma_tx_out.ident = target_asset.id
),
-- Fetch output UTXOs containing the token for these transactions
relevant_outputs AS (
    SELECT 
        tx_out.tx_id,
        jsonb_build_object(
            'tx_index', tx_out.index,
            'address', tx_out.address,
            'quantity', ma_tx_out.quantity
        ) AS utxo_info
    FROM relevant_tx_ids
    JOIN tx_out ON tx_out.tx_id = relevant_tx_ids.tx_id
    JOIN ma_tx_out ON ma_tx_out.tx_out_id = tx_out.id
    JOIN target_asset ON ma_tx_out.ident = target_asset.id
)
SELECT 
    encode(tx.hash, 'hex') AS tx_hash,
    COALESCE((
        SELECT jsonb_agg(utxo_info) 
        FROM relevant_inputs 
        WHERE relevant_inputs.tx_id = relevant_tx_ids.tx_id
    ), '[]'::jsonb) AS input_utxos,
    COALESCE((
        SELECT jsonb_agg(utxo_info) 
        FROM relevant_outputs 
        WHERE relevant_outputs.tx_id = relevant_tx_ids.tx_id
    ), '[]'::jsonb) AS output_utxos
FROM relevant_tx_ids
JOIN tx ON tx.id = relevant_tx_ids.tx_id
ORDER BY relevant_tx_ids.tx_id DESC;
