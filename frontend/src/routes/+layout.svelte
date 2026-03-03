<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { enhance } from '$app/forms';
	import type { LayoutData } from './$types';

	let { data, children }: { data: LayoutData; children: any } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if data.user}
	<header class="flex items-center justify-between p-4">
		<span class="font-semibold">{data.user.username}</span>
		<form method="POST" action="/?/logout" use:enhance>
			<button type="submit" class="btn preset-filled-surface-500">Logout</button>
		</form>
	</header>
{/if}

{@render children()}
