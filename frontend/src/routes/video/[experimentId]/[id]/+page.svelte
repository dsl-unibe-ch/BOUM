<script lang="ts">
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { authFetch } from '$lib/auth.svelte';
	import { PUBLIC_API_BASE_URL } from '$env/static/public';
	import { type VideoMetadata, emptyVideoMetadata } from '$lib/types';
	import MetadataForm from '$lib/components/MetadataForm.svelte';
	import PointCloudViewer from '$lib/components/PointCloudViewer.svelte';
	import VideoPlayer from '$lib/components/VideoPlayer.svelte';
	import { CirclePlay, LoaderCircle } from '@lucide/svelte';
	import { extractAudioFromVideo } from '$lib/audio';

	let { data }: { data: PageData } = $props();

	let metadata = $state<VideoMetadata>(data.video?.metadata ?? emptyVideoMetadata());
	let file = $state<File | null>(null);
	let saving = $state(false);
	let error = $state('');
	let saveMsg = $state('');
	let playerOpen = $state(false);
	let transcribing = $state(false);
	let transcribeMsg = $state('');
	let transcription = $state('');

	const isPlayable = $derived(
		data.video != null && data.video.status >= 1 && data.video.status <= 4
	);
	const STATUS_LABELS: Record<number, string> = {
		0: 'Pending',
		1: 'Seen',
		2: 'Checked',
		3: 'Processing',
		4: 'Processed',
		5: 'Failed'
	};

	async function handleFileChange(e: Event) {
		const input = e.target as HTMLInputElement;
		file = input.files?.[0] ?? null;
		if (!file) return;

		transcribing = true;
		transcribeMsg = '';
		transcription = '';
		try {
			const wavBlob = await extractAudioFromVideo(file);
			const formData = new FormData();
			formData.append('file', wavBlob, 'audio.wav');

			const res = await authFetch(`${PUBLIC_API_BASE_URL}/audio/`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				transcribeMsg = body?.msg ?? 'Transcription failed.';
				return;
			}

			const result = await res.json();
			if (result.metadata) {
				const m = result.metadata;
				metadata = {
					...metadata,
					title: m.title ?? metadata.title,
					species: m.species ?? metadata.species,
					cultivar: m.cultivar ?? metadata.cultivar,
					genotype: m.genotype ?? metadata.genotype,
					plant_age: m.plant_age ?? metadata.plant_age,
					plant_growth_stage: m.plant_growth_stage ?? metadata.plant_growth_stage,
					growth_environment: m.growth_environment ?? metadata.growth_environment,
					pot_volume: m.pot_volume ?? metadata.pot_volume,
					substrate_type: m.substrate_type ?? metadata.substrate_type,
					special_plant_treatments: m.special_plant_treatments ?? metadata.special_plant_treatments,
					operator: m.operator ?? metadata.operator
				};
				transcribeMsg = `Metadata filled from audio transcription.`;
				transcription = result.transcription;
			}
		} catch {
			transcribeMsg = 'Could not extract audio or reach transcription service.';
		} finally {
			transcribing = false;
		}
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

			const res = await authFetch(`${PUBLIC_API_BASE_URL}/experiment/${data.experimentId}/videos`, {
				method: 'POST',
				body: formData
			});

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				error = body?.msg ?? 'Failed to upload video.';
				return;
			}

			const videoData = await res.json();
			const metadataRes = await authFetch(
				`${PUBLIC_API_BASE_URL}/experiment/${data.experimentId}/videos/${videoData.id}/metadata`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify(metadata)
				}
			);

			if (!metadataRes.ok) {
				const body = await metadataRes.json().catch(() => null);
				error = body?.msg ?? 'Failed to save metadata.';
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
				`${PUBLIC_API_BASE_URL}/experiment/${data.experimentId}/videos/${data.video.id}/metadata`,
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

	async function deleteVideo() {
		if (!data.video) return;
		if (!confirm('Are you sure you want to delete this video? This action cannot be undone.')) {
			return;
		}

		saving = true;
		error = '';
		try {
			const res = await authFetch(
				`${PUBLIC_API_BASE_URL}/experiment/${data.experimentId}/videos/${data.video.id}`,
				{
					method: 'DELETE'
				}
			);

			if (!res.ok) {
				const body = await res.json().catch(() => null);
				error = body?.msg ?? 'Failed to delete video.';
				return;
			}

			await goto('/');
		} catch {
			error = 'Could not reach the server.';
		} finally {
			saving = false;
		}
	}
</script>

<div class="mx-auto max-w-2xl p-4">
	{#if data.mode === 'create'}
		<h1 class="mb-4 h2 font-bold">Upload new Video</h1>

		<form onsubmit={handleCreate} class="space-y-4 pb-20">
			<label class="label">
				<span class="label-text text-sm">Video File</span>
				<input class="input" type="file" accept="video/*" onchange={handleFileChange} required />
			</label>

			<h2 class="h4 font-semibold">Metadata</h2>

			{#if transcribing}
				<aside class="alert flex items-center gap-2 preset-filled-surface-500 text-sm">
					<LoaderCircle size={16} class="animate-spin" />
					<p>Transcribing audio to fill metadata…</p>
				</aside>
			{/if}

			{#if transcribeMsg}
				<aside class="alert preset-filled-surface-500 text-sm">
					<p>{transcribeMsg}</p>
					{#if transcription}
						<details class="mt-2">
							<summary class="cursor-pointer text-sm text-primary-800-200"
								>Show Transcription</summary
							>
							<pre
								class="mt-1 bg-surface-100-900 p-2 text-xs whitespace-pre-wrap">{transcription}</pre>
						</details>
					{/if}
				</aside>
			{/if}

			<MetadataForm bind:metadata disabled={saving && transcribing} />

			{#if error}
				<aside class="alert preset-filled-error-500"><p>{error}</p></aside>
			{/if}

			<div
				class="fixed inset-x-0 bottom-0 z-40 border-t border-surface-300-700 bg-surface-50-950 p-4"
			>
				<div class="mx-auto max-w-2xl">
					<button
						type="submit"
						class="btn w-full preset-filled-primary-500"
						disabled={saving && transcribing}
					>
						{#if saving}
							Uploading...
						{:else}
							Upload Video
						{/if}
					</button>
				</div>
			</div>
		</form>
	{:else if data.error}
		<aside class="alert preset-filled-error-500"><p>{data.error}</p></aside>
	{:else if data.video}
		<div class="mb-4 flex items-center gap-3">
			<h1 class="h2 font-bold">{data.video.metadata?.title ?? data.video.filename}</h1>
			{#if isPlayable}
				<button
					class="hover:text-primary-500"
					onclick={() => (playerOpen = true)}
					aria-label="Play video"
				>
					<CirclePlay size={30} />
				</button>
			{/if}
		</div>

		{#if isPlayable}
			<VideoPlayer
				experimentId={data.experimentId}
				videoId={data.video.id}
				bind:open={playerOpen}
			/>
		{/if}

		<div class="mb-4 card preset-outlined-surface-200-800 p-4">
			<p><strong>Status:</strong> {STATUS_LABELS[data.video.status] ?? 'Unknown'}</p>
			<p><strong>ID:</strong> {data.video.id}</p>
		</div>

		<h2 class="mb-2 h4 font-semibold">Point Cloud</h2>
		<div class="mb-4">
			<PointCloudViewer plyUrl="/only_mais.sog" />
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

			<button
				type="button"
				class="mt-3 btn preset-filled-error-500"
				onclick={deleteVideo}
				disabled={saving}
			>
				Delete Video
			</button>

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
