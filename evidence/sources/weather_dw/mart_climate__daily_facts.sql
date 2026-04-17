-- Últimos 12 meses de dados diários
-- 295 municípios × 365 dias ≈ 108.000 linhas (~15 MB Parquet)
-- Cobre um ciclo sazonal completo sem comprometer performance no browser
select * from marts.mart_climate__daily_facts
where date >= date_sub(current_date(), interval 12 month)
