import type { PageLoad } from './$types';
import { authFetch } from '$lib/auth.svelte';
import { API_BASE_URL } from '$lib/constants';
import type { VideoDetail } from '$lib/types';

export const load: PageLoad = async ({ params, fetch }) => {
	const experimentId = Number(params.experimentId);
	const videoId = params.id;

	if (videoId === 'new') {
		return { mode: 'create' as const, experimentId, video: null };
	}

	const res = await authFetch(
		`${API_BASE_URL}/experiment/${experimentId}/videos/${videoId}`,
		{},
		fetch
	);
	if (!res.ok) {
		return { mode: 'edit' as const, experimentId, video: null, error: 'Failed to load video.' };
	}

	// const video: VideoDetail = await res.json();
	const video: VideoDetail = { id: Number(videoId), filename: 'example.mp4', status: 0, metadata: null }; // Mock data for testing
	return { mode: 'edit' as const, experimentId, video };
};
