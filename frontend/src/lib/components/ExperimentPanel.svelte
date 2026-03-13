<script lang="ts">
	import { GripVerticalIcon, XIcon, MinusIcon, MaximizeIcon, MinimizeIcon } from '@lucide/svelte';
	import { FloatingPanel, Portal, useFloatingPanel } from '@skeletonlabs/skeleton-svelte';
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import { type ExperimentMetadata, type ExperimentDetail, emptyMetadata } from '$lib/types';

	let {
		experimentId,
		experimentName,
		open,
		onOpenChange
	}: {
		experimentId: number | null;
		experimentName: string;
		open: boolean;
		onOpenChange: (open: boolean) => void;
	} = $props();

	const id = $props.id();
	const panel = useFloatingPanel({
		id,
		onOpenChange: (details) => onOpenChange(details.open)
	});

	// Sync external `open` prop to zag-js via setOpen() to avoid batch crashes
	$effect(() => {
		const api = panel();
		if (open !== api.open) {
			api.setOpen(open);
		}
	});

	let loading = $state(false);
	let saving = $state(false);
	let error = $state('');
	let saveMsg = $state('');
	let metadata = $state<ExperimentMetadata>(emptyMetadata());
	let loadedId = $state<number | null>(null);

	$effect(() => {
		if (open && experimentId !== null && experimentId !== loadedId) {
			fetchExperiment();
		}
	});

	async function fetchExperiment() {
		loading = true;
		error = '';
		saveMsg = '';
		try {
			const res = await authFetch(`${API_BASE_URL}/experiment/${experimentId}`);
			if (!res.ok) {
				error = 'Failed to load experiment details.';
				return;
			}
			const data: ExperimentDetail = await res.json();
			metadata = data.metadata ?? emptyMetadata();
			loadedId = experimentId;
		} catch {
			error = 'Could not reach the server.';
		} finally {
			loading = false;
		}
	}

	async function handleSave(e: SubmitEvent) {
		e.preventDefault();
		saving = true;
		error = '';
		saveMsg = '';
		try {
			const res = await authFetch(`${API_BASE_URL}/experiment/${experimentId}/metadata`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(metadata)
			});
			if (!res.ok) {
				const body = await res.json().catch(() => null);
				error = body?.msg ?? 'Failed to save metadata.';
				return;
			}
			saveMsg = 'Metadata saved.';
		} catch {
			error = 'Could not reach the server.';
		} finally {
			saving = false;
		}
	}

	const fields: { key: keyof ExperimentMetadata; label: string; type: string }[] = [
		{ key: 'title', label: 'Title', type: 'text' },
		{ key: 'species', label: 'Species', type: 'text' },
		{ key: 'cultivar', label: 'Cultivar', type: 'text' },
		{ key: 'genotype', label: 'Genotype', type: 'text' },
		{ key: 'plant_age', label: 'Plant Age', type: 'text' },
		{ key: 'plant_growth_stage', label: 'Plant Growth Stage', type: 'text' },
		{ key: 'growth_environment', label: 'Growth Environment', type: 'text' },
		{ key: 'pot_volume', label: 'Pot Volume', type: 'number' },
		{ key: 'substrate_type', label: 'Substrate Type', type: 'text' },
		{ key: 'special_plant_treatments', label: 'Special Plant Treatments', type: 'text' },
		{ key: 'operator', label: 'Operator', type: 'text' },
		{ key: 'creation_date', label: 'Creation Date', type: 'datetime-local' }
	];
</script>

<FloatingPanel.Provider value={panel}>
	<Portal>
		<FloatingPanel.Positioner class="z-50">
			<FloatingPanel.Content class="flex flex-col">
				<FloatingPanel.DragTrigger>
					<FloatingPanel.Header>
						<FloatingPanel.Title>
							<GripVerticalIcon class="size-4" />
							{experimentName}
						</FloatingPanel.Title>
						<FloatingPanel.Control>
							<FloatingPanel.StageTrigger stage="minimized">
								<MinusIcon class="size-4" />
							</FloatingPanel.StageTrigger>
							<FloatingPanel.StageTrigger stage="maximized">
								<MaximizeIcon class="size-4" />
							</FloatingPanel.StageTrigger>
							<FloatingPanel.StageTrigger stage="default">
								<MinimizeIcon class="size-4" />
							</FloatingPanel.StageTrigger>
							<FloatingPanel.CloseTrigger>
								<XIcon class="size-4" />
							</FloatingPanel.CloseTrigger>
						</FloatingPanel.Control>
					</FloatingPanel.Header>
				</FloatingPanel.DragTrigger>
				<FloatingPanel.Body class="min-h-0 flex-1 overflow-y-auto p-4">
					{#if loading}
						<div class="flex items-center justify-center py-8">
							<p class="text-sm opacity-60">Loading...</p>
						</div>
					{:else if error}
						<aside class="alert mb-4 preset-filled-error-500"><p>{error}</p></aside>
					{/if}

					{#if loadedId !== null && !loading}
						<form onsubmit={handleSave} class="space-y-3">
							{#each fields as field (field.key)}
								<label class="label">
									<span class="label-text text-sm">{field.label}</span>
									{#if field.type === 'number'}
										<input
											class="input"
											type="number"
											step="any"
											bind:value={metadata[field.key]}
											placeholder={field.label}
										/>
									{:else if field.type === 'datetime-local'}
										<input class="input" type="datetime-local" bind:value={metadata[field.key]} />
									{:else}
										<input
											class="input"
											type="text"
											bind:value={metadata[field.key]}
											placeholder={field.label}
										/>
									{/if}
								</label>
							{/each}

							{#if saveMsg}
								<aside class="alert preset-filled-surface-500 text-sm"><p>{saveMsg}</p></aside>
							{/if}

							<button type="submit" class="btn w-full preset-filled-primary-500" disabled={saving}>
								{#if saving}
									Saving...
								{:else}
									Save Metadata
								{/if}
							</button>
						</form>
					{/if}
				</FloatingPanel.Body>
				<FloatingPanel.ResizeTrigger axis="se" />
			</FloatingPanel.Content>
		</FloatingPanel.Positioner>
	</Portal>
</FloatingPanel.Provider>
