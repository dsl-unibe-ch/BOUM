<script lang="ts">
	import { XIcon } from '@lucide/svelte';
	import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
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

	function handleOpenChange(details: { open: boolean }) {
		onOpenChange(details.open);
	}

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

	async function deleteExperiment() {
		if (
			!confirm('Are you sure you want to delete this experiment? This action cannot be undone.')
		) {
			return;
		}

		saving = true;
		error = '';
		try {
			const res = await authFetch(`${API_BASE_URL}/experiment/${experimentId}`, {
				method: 'DELETE'
			});

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				error = body?.msg ?? 'Failed to delete experiment.';
				return;
			}

			onOpenChange(false);
			invalidateAll();
		} catch {
			error = 'Could not reach the server.';
		} finally {
			saving = false;
		}
	}
</script>

<Dialog {open} onOpenChange={handleOpenChange}>
	<Portal>
		<Dialog.Backdrop class="fixed inset-0 z-50 bg-surface-50-950/50" />
		<Dialog.Positioner class="fixed inset-0 z-50 flex items-center justify-center p-4">
			<Dialog.Content
				class="flex max-h-[80vh] w-full max-w-xl flex-col space-y-4 card bg-surface-100-900 p-4 shadow-xl"
			>
				<header class="flex items-center justify-between">
					<Dialog.Title class="text-lg font-bold">{experimentName}</Dialog.Title>
					<Dialog.CloseTrigger class="btn-icon hover:preset-tonal">
						<XIcon class="size-4" />
					</Dialog.CloseTrigger>
				</header>

				{#if loading}
					<div class="flex items-center justify-center py-8">
						<p class="text-sm opacity-60">Loading...</p>
					</div>
				{:else if error}
					<aside class="alert mb-4 preset-filled-error-500"><p>{error}</p></aside>
				{/if}

				{#if loadedId !== null && !loading}
					<form onsubmit={handleSave} class="flex min-h-0 flex-col space-y-3">
						<div class="max-h-full min-h-0 overflow-y-auto">
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
							<button
								type="button"
								class="mt-3 btn preset-filled-error-500"
								onclick={deleteExperiment}
								disabled={saving}
							>
								Delete Experiment
							</button>

							{#if saveMsg}
								<aside class="alert preset-filled-surface-500 text-sm">
									<p>{saveMsg}</p>
								</aside>
							{/if}
						</div>
						<button type="submit" class="btn w-full preset-filled-primary-500" disabled={saving}>
							{#if saving}
								Saving...
							{:else}
								Save
							{/if}
						</button>
					</form>
				{/if}
			</Dialog.Content>
		</Dialog.Positioner>
	</Portal>
</Dialog>
