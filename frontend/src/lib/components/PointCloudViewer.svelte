<script lang="ts">
	import { Canvas } from '@threlte/core';
	import PointCloudScene from './PointCloudScene.svelte';

	let { plyUrl }: { plyUrl: string } = $props();
</script>

<div class="aspect-video w-full overflow-hidden rounded-lg border border-surface-300-700">
	<Canvas>
		<PointCloudScene {plyUrl} />
	</Canvas>
</div>
