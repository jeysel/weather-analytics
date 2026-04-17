-- Últimos 30 dias de dados horários
-- 295 municípios × 24h × 30 dias ≈ 212.000 linhas
-- Janela suficiente para análises intradiárias sem sobrecarregar o browser
select * from marts.mart_climate__hourly_facts
where date >= date_sub(current_date(), interval 30 day)
