<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
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
					<li class="card preset-outlined-surface-200-800 p-4">{exp.name}</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}
