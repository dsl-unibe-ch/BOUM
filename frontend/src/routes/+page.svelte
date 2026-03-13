<script lang="ts">
	import type { PageData } from './$types';
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import { invalidateAll } from '$app/navigation';
	import ExperimentPanel from '$lib/components/ExperimentPanel.svelte';

	let { data }: { data: PageData } = $props();

	let newName = $state('');
	let creating = $state(false);
	let createError = $state('');
	let selectedExp = $state<{ id: number; name: string } | null>(null);
	let panelOpen = $state(false);

	async function createExperiment(e: SubmitEvent) {
		e.preventDefault();
		createError = '';
		creating = true;

		try {
			const res = await authFetch(`${API_BASE_URL}/experiment/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: newName })
			});

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				createError = body?.msg ?? 'Failed to create experiment.';
				return;
			}

			newName = '';
			await invalidateAll();
		} catch {
			createError = 'Could not reach the server.';
		} finally {
			creating = false;
		}
	}
</script>

{#if data.error}
	<aside class="alert m-4 preset-filled-error-500"><p>{data.error}</p></aside>
{:else}
	<div class="p-4">
		<h1 class="mb-4 h2 font-bold">Experiments</h1>
		{#if data.experiments.length === 0}
			<p>No experiments found.</p>
		{:else}
			<ul class="space-y-2">
				{#each data.experiments as exp (exp.id)}
					<li class="card preset-outlined-surface-200-800 p-4">
						<button
							type="button"
							class="cursor-pointer h4 font-bold hover:underline"
							onclick={() => {
								if (selectedExp?.id === exp.id) {
									panelOpen = !panelOpen;
								} else {
									selectedExp = exp;
									panelOpen = true;
								}
							}}
						>
							{exp.name}
						</button>
						{#if exp.videos?.length}
							<ul class="mt-2 space-y-1 pl-4">
								{#each exp.videos as video (video.id)}
									<li>
										<a href="/videos/{video.id}" class="anchor">
											{video.title || `${exp.name} ${video.id}`}
										</a>
									</li>
								{/each}
							</ul>
						{:else}
							<p class="mt-2 text-sm opacity-60">No videos</p>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}

<ExperimentPanel
	experimentId={selectedExp?.id ?? null}
	experimentName={selectedExp?.name ?? ''}
	open={panelOpen}
	onOpenChange={(isOpen) => {
		panelOpen = isOpen;
		if (!isOpen) selectedExp = null;
	}}
/>

<form onsubmit={createExperiment} class="mb-6 flex gap-2">
	<input
		class="input flex-1"
		type="text"
		bind:value={newName}
		placeholder="New experiment name"
		required
		minlength={1}
		maxlength={100}
	/>
	<button type="submit" class="btn preset-filled-primary-500" disabled={creating}>
		{#if creating}
			Creating...
		{:else}
			Create
		{/if}
	</button>
</form>

{#if createError}
	<aside class="alert mb-4 preset-filled-error-500"><p>{createError}</p></aside>
{/if}
