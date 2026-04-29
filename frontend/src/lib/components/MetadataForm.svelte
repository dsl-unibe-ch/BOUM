<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Combobox,
		Portal,
		type ComboboxRootProps,
		useListCollection
	} from '@skeletonlabs/skeleton-svelte';
	import type { MetadataDefaults, VideoMetadata } from '$lib/types';

	let {
		metadata = $bindable(),
		disabled = false,
		mode = 'video'
	}: {
		metadata: MetadataDefaults | VideoMetadata;
		disabled?: boolean;
		mode?: 'experiment' | 'video';
	} = $props();

	type TextFieldKey =
		| 'title'
		| 'species'
		| 'cultivar'
		| 'genotype'
		| 'plant_age'
		| 'plant_growth_stage'
		| 'growth_environment'
		| 'substrate_type'
		| 'special_plant_treatments'
		| 'operator';

	type FieldDef = {
		key: TextFieldKey | 'pot_volume' | 'creation_date';
		label: string;
		type: 'text' | 'number' | 'datetime-local';
	};

	type ComboboxItem = { label: string; value: string };
	type SuggestionStore = Partial<Record<TextFieldKey, string[]>>;

	const STORAGE_KEY = 'metadata-form-suggestions-v1';
	const SUGGESTION_LIMIT = 10;
	const TEXT_FIELD_KEYS: TextFieldKey[] = [
		'title',
		'species',
		'cultivar',
		'genotype',
		'plant_age',
		'plant_growth_stage',
		'growth_environment',
		'substrate_type',
		'special_plant_treatments',
		'operator'
	];

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

	let optionsByField = $state<Partial<Record<TextFieldKey, string[]>>>({});
	let itemsByField = $state<Partial<Record<TextFieldKey, ComboboxItem[]>>>({});
	let openByField = $state<Partial<Record<TextFieldKey, boolean>>>({});

	const fields = $derived(
		mode === 'video' ? [videoOnlyFields[0], ...sharedFields, videoOnlyFields[1]] : sharedFields
	);

	onMount(() => {
		const stored = loadSuggestionStore();
		const nextOptions: Partial<Record<TextFieldKey, string[]>> = {};
		const nextItems: Partial<Record<TextFieldKey, ComboboxItem[]>> = {};

		for (const key of TEXT_FIELD_KEYS) {
			const values = normalizeSuggestions(stored[key] ?? []);
			nextOptions[key] = values;
			nextItems[key] = toComboboxItems(values);
		}

		optionsByField = nextOptions;
		itemsByField = nextItems;
		openByField = {};
	});

	function getTextValue(key: TextFieldKey): string {
		const value = (metadata as Record<string, unknown>)[key];
		return typeof value === 'string' ? value : '';
	}

	function setTextValue(key: TextFieldKey, value: string): void {
		(metadata as Record<string, unknown>)[key] = value;
	}

	function toComboboxItems(values: string[]): ComboboxItem[] {
		return values.map((value) => ({ label: value, value }));
	}

	function normalizeSuggestions(values: string[]): string[] {
		const unique: string[] = [];
		const seen = new Set<string>();

		for (const raw of values) {
			const value = raw.trim();
			if (!value) continue;
			const lowered = value.toLowerCase();
			if (seen.has(lowered)) continue;
			seen.add(lowered);
			unique.push(value);
			if (unique.length >= SUGGESTION_LIMIT) break;
		}

		return unique;
	}

	function loadSuggestionStore(): SuggestionStore {
		try {
			const raw = localStorage.getItem(STORAGE_KEY);
			if (!raw) return {};
			const parsed = JSON.parse(raw) as SuggestionStore;
			if (!parsed || typeof parsed !== 'object') return {};
			return parsed;
		} catch {
			return {};
		}
	}

	function saveSuggestionStore(store: SuggestionStore): void {
		try {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
		} catch {
			// Ignore storage errors (private mode/full storage).
		}
	}

	function persistTextValue(key: TextFieldKey, rawValue: string): void {
		const value = rawValue.trim();
		if (!value) return;

		const current = optionsByField[key] ?? [];
		const next = normalizeSuggestions([value, ...current]);

		optionsByField = { ...optionsByField, [key]: next };
		itemsByField = { ...itemsByField, [key]: toComboboxItems(next) };

		const store = loadSuggestionStore();
		store[key] = next;
		saveSuggestionStore(store);
	}

	function getCollection(key: TextFieldKey) {
		return useListCollection({
			items: itemsByField[key] ?? [],
			itemToString: (item) => item.label,
			itemToValue: (item) => item.value
		});
	}

	function onOpenChange(key: TextFieldKey): ComboboxRootProps['onOpenChange'] {
		return (event) => {
			openByField = {
				...openByField,
				[key]: event.open
			};

			const options = optionsByField[key] ?? [];
			itemsByField = {
				...itemsByField,
				[key]: toComboboxItems(options)
			};
		};
	}

	// Let Combobox handle Enter selection, but avoid bubbling to parent form handlers.
	function onComboboxInputKeyDown(key: TextFieldKey, event: KeyboardEvent): void {
		if (event.key !== 'Enter') return;
		if (!openByField[key]) return;
		event.stopPropagation();
	}

	function onInputValueChange(key: TextFieldKey): ComboboxRootProps['onInputValueChange'] {
		return (event) => {
			const inputValue = event.inputValue ?? '';
			setTextValue(key, inputValue);

			const query = inputValue.trim().toLowerCase();
			const options = optionsByField[key] ?? [];
			const filtered =
				query.length === 0
					? options
					: options.filter((option) => option.toLowerCase().includes(query));

			itemsByField = {
				...itemsByField,
				[key]: toComboboxItems(filtered)
			};
		};
	}

	function onValueChange(key: TextFieldKey): ComboboxRootProps['onValueChange'] {
		return (event) => {
			const selected = event.value?.[0] ?? '';
			setTextValue(key, selected);
			if (selected) {
				persistTextValue(key, selected);
			}
		};
	}
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
				{@const key = field.key as TextFieldKey}
				<Combobox
					class="w-full"
					collection={getCollection(key)}
					allowCustomValue
					inputBehavior="autohighlight"
					placeholder={field.label}
					inputValue={getTextValue(key)}
					onOpenChange={onOpenChange(key)}
					onInputValueChange={onInputValueChange(key)}
					onValueChange={onValueChange(key)}
					{disabled}
				>
					<Combobox.Control>
						<Combobox.Input
							class="input"
							onkeydown={(event) => onComboboxInputKeyDown(key, event)}
							onchange={() => persistTextValue(key, getTextValue(key))}
							onblur={() => persistTextValue(key, getTextValue(key))}
						/>
						<Combobox.Trigger />
					</Combobox.Control>
					<Portal>
						<Combobox.Positioner>
							<Combobox.Content class="z-50 max-h-56 overflow-auto">
								{#each itemsByField[key] ?? [] as item (item.value)}
									<Combobox.Item {item}>
										<Combobox.ItemText>{item.label}</Combobox.ItemText>
										<Combobox.ItemIndicator />
									</Combobox.Item>
								{/each}
							</Combobox.Content>
						</Combobox.Positioner>
					</Portal>
				</Combobox>
			{/if}
		</label>
	{/each}
</div>
