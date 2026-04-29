<script lang="ts">
	import { T, useThrelte, useTask } from '@threlte/core';
	import { SparkRenderer, SplatMesh } from '@sparkjsdev/spark';
	import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
	import { authFetch } from '$lib/auth.svelte';

	let { plyUrl }: { plyUrl: string } = $props();

	const { renderer, invalidate } = useThrelte();
	const sparkRenderer = new SparkRenderer({ renderer });
	let fileBytes = $derived(authFetch(plyUrl).then((res) => res.arrayBuffer()));

	let splatMesh = $state<SplatMesh | null>(null);

	$effect(() => {
		fileBytes.then((bytes) => {
			splatMesh = new SplatMesh({ fileBytes: bytes });
		});
	});

	let controls: OrbitControls | undefined;

	useTask(() => {
		if (controls) {
			controls.update();
			invalidate();
		}
	});
</script>

<T.PerspectiveCamera
	makeDefault
	position={[0, 2, 5]}
	fov={60}
	oncreate={(ref) => ref.lookAt(0, 0, 0)}
>
	{#snippet children({ ref })}
		<T
			is={OrbitControls}
			args={[ref, renderer.domElement]}
			enableDamping
			oncreate={(c) => {
				controls = c;
			}}
		/>
	{/snippet}
</T.PerspectiveCamera>

<T is={sparkRenderer} />
{#if splatMesh}
	<T is={splatMesh} rotation.x={-1.6} position.y={1.2} />
{/if}
<!-- <T.GridHelper args={[10, 10]} /> -->
