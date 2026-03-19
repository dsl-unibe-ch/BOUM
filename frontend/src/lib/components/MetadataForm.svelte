<script lang="ts">
	import type { ExperimentMetadataDefaults, VideoMetadata } from '$lib/types';

	let {
		metadata = $bindable(),
		disabled = false,
		mode = 'video'
	}: {
		metadata: ExperimentMetadataDefaults | VideoMetadata;
		disabled?: boolean;
		mode?: 'experiment' | 'video';
	} = $props();

	type FieldDef = { key: string; label: string; type: string };

	const sharedFields: FieldDef[] = [
		{ key: 'species', label: 'Species', type: 'text' },
		{ key: 'cultivar', label: 'Cultivar', type: 'text' },
		{ key: 'genotype', label: 'Genotype', type: 'text' },
		{ key: 'plant_age', label: 'Plant Age', type: 'text' },
		{ key: 'plant_growth_stage', label: 'Plant Growth Stage', type: 'text' },
		{ key: 'growth_environment', label: 'Growth Environment', type: 'text' },
		{ key: 'pot_volume', label: 'Pot Volume', type: 'number' },
		{ key: 'substrate_type', label: 'Substrate Type', type: 'text' },
		{ key: 'special_plant_treatments', label: 'Special Plant Treatments', type: 'text' },
		{ key: 'operator', label: 'Operator', type: 'text' }
	];

	const videoOnlyFields: FieldDef[] = [
		{ key: 'title', label: 'Title', type: 'text' },
		{ key: 'creation_date', label: 'Creation Date', type: 'datetime-local' }
	];

	const fields = $derived(
		mode === 'video' ? [videoOnlyFields[0], ...sharedFields, videoOnlyFields[1]] : sharedFields
	);
</script>

<div class="space-y-3">
	{#each fields as field (field.key)}
		<label class="label">
			<span class="label-text text-sm">{field.label}</span>
			{#if field.type === 'number'}
				<input
					class="input"
					type="number"
					step="any"
					bind:value={(metadata as Record<string, any>)[field.key]}
					placeholder={field.label}
					{disabled}
				/>
			{:else if field.type === 'datetime-local'}
				<input
					class="input"
					type="datetime-local"
					bind:value={(metadata as Record<string, any>)[field.key]}
					{disabled}
				/>
			{:else}
				<input
					class="input"
					type="text"
					bind:value={(metadata as Record<string, any>)[field.key]}
					placeholder={field.label}
					{disabled}
				/>
			{/if}
		</label>
	{/each}
</div>
