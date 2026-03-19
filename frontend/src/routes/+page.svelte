<script lang="ts">
	import { invalidateAll } from '$app/navigation';
	import { ChevronDownIcon } from '@lucide/svelte';
	import { Accordion } from '@skeletonlabs/skeleton-svelte';
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import type { ExperimentDetail } from '$lib/types';
	import type { PageData } from './$types';
	import ExperimentPanel from '$lib/components/ExperimentPanel.svelte';

	type DetailState = {
		loading: boolean;
		error: string;
		data: ExperimentDetail | null;
	};

	let { data }: { data: PageData } = $props();

	let newName = $state('');
	let creating = $state(false);
	let createError = $state('');
	let openItems = $state<string[]>([]);
	let detailsByExperiment = $state<Record<number, DetailState>>({});
	let selectedExp = $state<{ id: number; name: string } | null>(null);
	let panelOpen = $state(false);

	const STATUS_LABELS: Record<number, string> = {
		0: 'Pending',
		1: 'Seen',
		2: 'Checked',
		3: 'Processing',
		4: 'Processed',
		5: 'Failed'
	};

	function getDetailState(experimentId: number): DetailState {
		return detailsByExperiment[experimentId] ?? { loading: false, error: '', data: null };
	}

	function setDetailState(experimentId: number, state: DetailState) {
		detailsByExperiment = { ...detailsByExperiment, [experimentId]: state };
	}

	async function ensureExperimentLoaded(experimentId: number) {
		const currentState = getDetailState(experimentId);
		if (currentState.loading || currentState.data) return;

		setDetailState(experimentId, { loading: true, error: '', data: null });

		try {
			const res = await authFetch(`${API_BASE_URL}/experiment/${experimentId}`);

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				setDetailState(experimentId, {
					loading: false,
					error: body?.msg ?? 'Failed to load experiment details.',
					data: null
				});
				return;
			}

			const experimentDetail: ExperimentDetail = await res.json();
			setDetailState(experimentId, {
				loading: false,
				error: '',
				data: experimentDetail
			});
		} catch {
			setDetailState(experimentId, {
				loading: false,
				error: 'Could not reach the server.',
				data: null
			});
		}
	}

	async function handleAccordionChange(details: { value: string[] }) {
		const previousItems = new Set(openItems);
		openItems = details.value;

		for (const item of details.value) {
			if (!previousItems.has(item)) {
				const experimentId = Number(item);
				if (!Number.isNaN(experimentId)) {
					await ensureExperimentLoaded(experimentId);
				}
			}
		}
	}

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

<div class="p-4">
	<h1 class="mb-4 h2 font-bold">Experiments</h1>

	{#if data.error}
		<aside class="alert mb-4 preset-filled-error-500"><p>{data.error}</p></aside>
	{:else if data.experiments.length === 0}
		<p class="mb-6">No experiments found.</p>
	{:else}
		<div class="mb-6 card preset-outlined-surface-200-800">
			<Accordion collapsible value={openItems} onValueChange={handleAccordionChange}>
				{#each data.experiments as exp, index (exp.id)}
					{#if index !== 0}
						<hr class="hr" />
					{/if}

					{@const detailState = getDetailState(exp.id)}

					<Accordion.Item value={String(exp.id)}>
						<h2>
							<Accordion.ItemTrigger
								class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left font-bold"
							>
								<span>{exp.name}{exp.start_date ? ` (${exp.start_date})` : ''}</span>
								<a href="/video/{exp.id}/new" class="btn preset-filled-primary-500">
									Upload new Video
								</a>
								<button
									type="button"
									class="btn preset-filled-primary-500"
									onclick={() => {
										if (selectedExp?.id === exp.id) {
											panelOpen = !panelOpen;
										} else {
											selectedExp = exp;
											panelOpen = true;
										}
									}}
								>
									edit metadata & defaults
								</button>
								<Accordion.ItemIndicator class="group shrink-0">
									<ChevronDownIcon class="size-5 transition group-data-[state=open]:rotate-180" />
								</Accordion.ItemIndicator>
							</Accordion.ItemTrigger>
						</h2>

						<Accordion.ItemContent>
							{#snippet element(attributes)}
								{#if !attributes.hidden}
									<div {...attributes} class="space-y-4 px-4 pb-4">
										{#if detailState.loading}
											<p class="text-sm opacity-60">Loading videos...</p>
										{:else if detailState.error}
											<aside class="alert preset-filled-error-500">
												<p>{detailState.error}</p>
											</aside>
										{:else if detailState.data}
											{#if detailState.data.videos.length === 0}
												<p class="text-sm opacity-60">No videos</p>
											{:else}
												<ul class="space-y-2">
													{#each detailState.data.videos as video (video.id)}
														<li
															class="flex items-center justify-between gap-3 rounded-base border p-3"
														>
															<a href="/video/{exp.id}/{video.id}" class="anchor font-medium">
																{video.filename || `Video ${video.id}`}
															</a>
															<span class="text-sm opacity-60">
																{STATUS_LABELS[video.status] ?? 'Unknown'}
															</span>
														</li>
													{/each}
												</ul>
											{/if}
										{/if}
									</div>
								{/if}
							{/snippet}
						</Accordion.ItemContent>
					</Accordion.Item>
				{/each}
			</Accordion>
		</div>
	{/if}

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

	<ExperimentPanel
		experimentId={selectedExp?.id ?? null}
		experimentName={selectedExp?.name ?? ''}
		open={panelOpen}
		onOpenChange={(isOpen) => {
			panelOpen = isOpen;
			if (!isOpen) selectedExp = null;
		}}
	/>
</div>
