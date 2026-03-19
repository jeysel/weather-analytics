// Configuração adicional do SvelteKit para o projeto Evidence.
// Evidence.dev mescla este arquivo com o svelte.config.js interno do template.
// Necessário para pré-renderizar as rotas dinâmicas /cidades/[cidade].

export default {
	kit: {
		prerender: {
			entries: [
				'*',
				'/cidades/florianopolis',
				'/cidades/palhoca',
				'/cidades/santo_amaro_da_imperatriz',
				'/cidades/angelina',
				'/cidades/garopaba',
				'/cidades/imbituba',
				'/cidades/laguna',
				'/cidades/tubarao',
				'/cidades/criciuma',
				'/cidades/ararangua',
				'/cidades/lages',
				'/cidades/campos_novos',
				'/cidades/balneario_camboriu',
				'/cidades/itajai',
				'/cidades/joinville',
				'/cidades/chapeco',
				'/cidades/sao_miguel_do_oeste'
			]
		}
	}
};
