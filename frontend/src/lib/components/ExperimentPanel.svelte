<script lang="ts">
	import { GripVerticalIcon, XIcon, MinusIcon, MaximizeIcon, MinimizeIcon } from '@lucide/svelte';
	import { FloatingPanel, Portal, useFloatingPanel } from '@skeletonlabs/skeleton-svelte';
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import { type MetadataDefaults, type ExperimentDetail } from '$lib/types';
	import MetadataForm from '$lib/components/MetadataForm.svelte';
	import { invalidateAll } from '$app/navigation';

	const METADATA_KEYS: (keyof MetadataDefaults)[] = [
		'species',
		'cultivar',
		'genotype',
		'plant_age',
		'plant_growth_stage',
		'growth_environment',
		'pot_volume',
		'substrate_type',
		'special_plant_treatments',
		'operator'
	];

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
		onOpenChange: (details) => onOpenChange(details.open),
		minSize: { width: 300, height: 200 },
		defaultSize: { width: 500, height: 500 }
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
	let name = $state('');
	let initName = $state('');
	let startDate = $state('');
	let initStartDate = $state('');
	let metadata = $state<MetadataDefaults>({});
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
			name = data.name;
			initName = data.name;
			startDate = data.start_date ?? '';
			initStartDate = data.start_date ?? '';
			metadata = data.metadata_defaults ?? {};
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
			const metadataPayload: Record<string, unknown> = {};
			for (const key of METADATA_KEYS) {
				if (metadata[key] !== undefined && metadata[key] !== '') {
					metadataPayload[key] = metadata[key];
				}
			}

			const experimentPayload: Record<string, unknown> = {};
			if (name && name !== initName) experimentPayload.name = name;
			if (startDate && startDate !== initStartDate) experimentPayload.start_date = startDate;

			const promises: Promise<Response>[] = [];

			if (Object.keys(metadataPayload).length > 0) {
				promises.push(
					authFetch(`${API_BASE_URL}/experiment/${experimentId}/metadata`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify(metadataPayload)
					})
				);
			}

			if (Object.keys(experimentPayload).length > 0) {
				promises.push(
					authFetch(`${API_BASE_URL}/experiment/${experimentId}`, {
						method: 'PUT',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify(experimentPayload)
					})
				);
			}

			if (promises.length === 0) {
				saveMsg = 'Nothing to save.';
				return;
			}

			const results = await Promise.all(promises);
			const failed = results.find((r) => !r.ok);
			if (failed) {
				const body = await failed.json().catch(() => null);
				error = body?.msg ?? 'Failed to save.';
				return;
			}
			saveMsg = 'Saved successfully.';
			if (Object.keys(experimentPayload).length > 0) {
				invalidateAll();
			}
		} catch {
			error = 'Could not reach the server.';
		} finally {
			saving = false;
		}
	}
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
				<FloatingPanel.Body class="max-h-full min-h-0 flex-1 px-4 pt-4">
					{#if loading}
						<div class="flex items-center justify-center py-8">
							<p class="text-sm opacity-60">Loading...</p>
						</div>
					{:else if error}
						<aside class="alert mb-4 preset-filled-error-500"><p>{error}</p></aside>
					{/if}

					{#if loadedId !== null && !loading}
						<form onsubmit={handleSave} class="flex max-h-full flex-col space-y-3">
							<div class="w-full overflow-y-auto">
								<label class="label">
									<span class="label-text text-sm">Experiment Name</span>
									<input
										class="input"
										type="text"
										bind:value={name}
										placeholder="Experiment Name"
										disabled={saving}
									/>
								</label>
								<label class="label">
									<span class="label-text text-sm">Start Date</span>
									<input
										class="input"
										type="datetime-local"
										bind:value={startDate}
										disabled={saving}
									/>
								</label>

								<hr class="hr" />
								<h2 class="h4 font-bold">Plant Default Metadata</h2>
								<MetadataForm bind:metadata disabled={saving} mode="experiment" />
							</div>
							{#if saveMsg}
								<aside class="alert preset-filled-surface-500 text-sm"><p>{saveMsg}</p></aside>
							{/if}

							<button type="submit" class="btn w-full preset-filled-primary-500" disabled={saving}>
								{#if saving}
									Saving...
								{:else}
									Save
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
