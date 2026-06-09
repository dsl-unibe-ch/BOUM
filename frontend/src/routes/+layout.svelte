<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { House } from '@lucide/svelte';
	import { logout } from '$lib/auth.svelte';
	import { page } from '$app/state';
	import type { LayoutData } from './$types';

	let { data, children }: { data: LayoutData; children: any } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if data.user}
	<header class="flex items-center justify-between p-4">
		<a href="/" class="btn-ghost btn gap-2">
			<House size={20} />
			<span class="hidden sm:inline">Home</span>
		</a>
		<span class="font-semibold">{data.user.username}</span>
		<button onclick={logout} class="btn preset-filled-surface-500">Logout</button>
	</header>
{/if}

{#key page.url.pathname}
	<div class="container mx-auto mt-6">
		{@render children()}
	</div>
{/key}
