<script lang="ts">
	import { T, useThrelte, useTask } from '@threlte/core';
	import { SplatMesh, SparkRenderer } from '@sparkjsdev/spark';
	import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

	let { plyUrl }: { plyUrl: string } = $props();

	const { renderer, invalidate } = useThrelte();
	const spark = new SparkRenderer({ renderer });
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
	position={[0, 0, 5]}
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

<T is={spark} />
<T is={splatMesh} />
