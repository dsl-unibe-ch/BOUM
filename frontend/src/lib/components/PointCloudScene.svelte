<script lang="ts">
	import { T, useThrelte, useTask } from '@threlte/core';
	import { SplatMesh } from '@sparkjsdev/spark';
	import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

	let { plyUrl }: { plyUrl: string } = $props();

	const { renderer, invalidate } = useThrelte();
	const splatMesh = new SplatMesh({ url: plyUrl });

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

<T is={splatMesh} rotation.x={1.3} rotation.y={-0.95} position.y={4.8} />
<!-- <T.GridHelper args={[10, 10]} /> -->
