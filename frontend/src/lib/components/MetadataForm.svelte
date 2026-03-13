<script lang="ts">
	import type { ExperimentMetadata } from '$lib/types';

	let {
		metadata = $bindable(),
		disabled = false
	}: {
		metadata: ExperimentMetadata;
		disabled?: boolean;
	} = $props();

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

<div class="space-y-3">
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
					{disabled}
				/>
			{:else if field.type === 'datetime-local'}
				<input class="input" type="datetime-local" bind:value={metadata[field.key]} {disabled} />
			{:else}
				<input
					class="input"
					type="text"
					bind:value={metadata[field.key]}
					placeholder={field.label}
					{disabled}
				/>
			{/if}
		</label>
	{/each}
</div>
