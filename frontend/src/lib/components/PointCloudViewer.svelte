<script lang="ts">
	import { Canvas } from '@threlte/core';
	import PointCloudScene from './PointCloudScene.svelte';
	import { Fullscreen, Maximize2, Minimize, Minimize2 } from '@lucide/svelte';

	let { plyUrl }: { plyUrl: string } = $props();

	let container: HTMLDivElement;
	let enlarged = $state(false);
	let isFullscreen = $state(false);

	function toggleFullscreen() {
		if (isFullscreen) {
			document.exitFullscreen();
		} else {
			container.requestFullscreen();
		}
	}
</script>

<div
	bind:this={container}
	onfullscreenchange={() => (isFullscreen = document.fullscreenElement === container)}
	class="aspect-video overflow-hidden rounded-lg border border-surface-300-700 {enlarged
		? 'relative left-1/2 w-screen -translate-x-1/2'
		: 'w-full'}"
>
<div class="absolute flex space-x-2">
	<button class="z-10 btn-icon preset-outlined-surface-300-700" onclick={toggleFullscreen}>
		{#if isFullscreen}
			<Minimize />
		{:else}
			<Fullscreen />
		{/if}
	</button>
	{#if !isFullscreen}
		<button class="z-10 btn-icon preset-outlined-surface-300-700" onclick={() => (enlarged = !enlarged)}>
			{#if enlarged}
				<Minimize2 />
			{:else}
				<Maximize2 />
			{/if}
		</button>
	{/if}
</div>
	<Canvas>
		<PointCloudScene {plyUrl} />
	</Canvas>
</div>
