import base from '../../eslint.config.js';
import prettier from 'eslint-config-prettier';
import svelte from 'eslint-plugin-svelte';

export default [
	{ ignores: ['.svelte-kit/', 'build/', 'dist/'] },
	...base,
	prettier,
	...svelte.configs.prettier
];
