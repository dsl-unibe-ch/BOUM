<script lang="ts">
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { authFetch } from '$lib/auth.svelte';
	import { API_BASE_URL } from '$lib/constants';
	import { type ExperimentMetadata, emptyMetadata } from '$lib/types';
	import MetadataForm from '$lib/components/MetadataForm.svelte';

	let { data }: { data: PageData } = $props();

	let metadata = $state<ExperimentMetadata>(data.video?.metadata ?? emptyMetadata());
	let file = $state<File | null>(null);
	let saving = $state(false);
	let error = $state('');
	let saveMsg = $state('');

	const STATUS_LABELS: Record<number, string> = {
		0: 'Pending',
		1: 'Seen',
		2: 'Checked',
		3: 'Processing',
		4: 'Processed',
		5: 'Failed'
	};

	function handleFileChange(e: Event) {
		const input = e.target as HTMLInputElement;
		file = input.files?.[0] ?? null;
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		if (!file) {
			error = 'Please select a video file.';
			return;
		}
		saving = true;
		error = '';
		try {
			const formData = new FormData();
			formData.append('file', file);
			formData.append('metadata', JSON.stringify(metadata));

			const res = await authFetch(`${API_BASE_URL}/experiment/${data.experimentId}/videos`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				error = body?.msg ?? 'Failed to upload video.';
				return;
			}

			await goto('/');
		} catch {
			error = 'Could not reach the server.';
		} finally {
			saving = false;
		}
	}

	async function handleSaveMetadata(e: SubmitEvent) {
		e.preventDefault();
		if (!data.video) return;
		saving = true;
		error = '';
		saveMsg = '';
		try {
			const res = await authFetch(
				`${API_BASE_URL}/experiment/${data.experimentId}/videos/${data.video.id}/metadata`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(metadata)
				}
			);

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
</script>

<div class="mx-auto max-w-2xl p-4">
	<a href="/" class="mb-4 inline-block anchor">&larr; Back to experiments</a>

	{#if data.mode === 'create'}
		<h1 class="mb-4 h2 font-bold">Upload new Video</h1>

		<form onsubmit={handleCreate} class="space-y-4">
			<label class="label">
				<span class="label-text text-sm">Video File</span>
				<input class="input" type="file" accept="video/*" onchange={handleFileChange} required />
			</label>

			<h2 class="h4 font-semibold">Metadata</h2>
			<MetadataForm bind:metadata disabled={saving} />

			{#if error}
				<aside class="alert preset-filled-error-500"><p>{error}</p></aside>
			{/if}

			<button type="submit" class="btn w-full preset-filled-primary-500" disabled={saving}>
				{#if saving}
					Uploading...
				{:else}
					Upload Video
				{/if}
			</button>
		</form>
	{:else if data.error}
		<aside class="alert preset-filled-error-500"><p>{data.error}</p></aside>
	{:else if data.video}
		<h1 class="mb-4 h2 font-bold">{data.video.filename}</h1>

		<div class="mb-4 card preset-outlined-surface-200-800 p-4">
			<p><strong>Status:</strong> {STATUS_LABELS[data.video.status] ?? 'Unknown'}</p>
			<p><strong>ID:</strong> {data.video.id}</p>
		</div>

		<h2 class="mb-2 h4 font-semibold">Metadata</h2>

		<form onsubmit={handleSaveMetadata} class="space-y-4">
			<MetadataForm bind:metadata disabled={saving} />

			{#if error}
				<aside class="alert preset-filled-error-500"><p>{error}</p></aside>
			{/if}

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
</div>
