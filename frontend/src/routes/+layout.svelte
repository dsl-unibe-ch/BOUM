<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { House, RotateCcwKey } from '@lucide/svelte';
	import { logout } from '$lib/auth.svelte';
	import { page } from '$app/state';
	import ChangePasswordPanel from '$lib/components/ChangePasswordPanel.svelte';
	import type { LayoutData } from './$types';

	let { data, children }: { data: LayoutData; children: any } = $props();

	let passwordPanelOpen = $state(false);
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

{#if data.user}
	<header class="flex items-center justify-between p-4 flex-wrap">
		<a href="/" class="btn-ghost btn gap-2">
			<House size={20} />
			<span class="hidden sm:inline">Home</span>
		</a>
		<span class="font-semibold"
			>{data.user.username}
			<button
				class="btn-icon preset-outlined-primary-500"
				onclick={() => (passwordPanelOpen = true)}
				aria-label="Change password"><RotateCcwKey size={16} /></button
			></span
		>
		{#if data.user.role === 0}
			<a href="/users" class="btn preset-filled-surface-500">user admin</a>
		{/if}
		<button onclick={logout} class="btn preset-filled-surface-500">Logout</button>
	</header>

	<ChangePasswordPanel
		selectedUserId={String(data.user.id)}
		open={passwordPanelOpen}
		onOpenChange={(isOpen) => (passwordPanelOpen = isOpen)}
	/>
{/if}

{#key page.url.pathname}
	<div class="container mx-auto mt-6">
		{@render children()}
	</div>
{/key}
