export interface ExperimentMetadataDefaults {
	species: string;
	cultivar: string;
	genotype: string;
	plant_age: string;
	plant_growth_stage: string;
	growth_environment: string;
	pot_volume: number | null;
	substrate_type: string;
	special_plant_treatments: string;
	operator: string;
}

export interface VideoMetadata extends ExperimentMetadataDefaults {
	title: string;
	creation_date: string;
}

export interface ExperimentListItem {
	id: number;
	name: string;
	start_date: string | null;
	video_count: number;
	user_count?: number;
}

export interface ExperimentVideo {
	id: number;
	filename: string;
	path: string;
	status: number;
	experiment_id: number;
	metadata: VideoMetadata | null;
}

export interface ExperimentUser {
	id: number;
	username: string;
}

export interface ExperimentDetail {
	id: number;
	name: string;
	start_date: string | null;
	users: ExperimentUser[];
	videos: ExperimentVideo[];
	metadata_defaults: ExperimentMetadataDefaults | null;
}

export interface VideoDetail {
	id: number;
	filename: string;
	status: number;
	download_url: string;
	metadata: VideoMetadata | null;
}

export function emptyMetadataDefaults(): ExperimentMetadataDefaults {
	return {
		species: '',
		cultivar: '',
		genotype: '',
		plant_age: '',
		plant_growth_stage: '',
		growth_environment: '',
		pot_volume: null,
		substrate_type: '',
		special_plant_treatments: '',
		operator: ''
	};
}

export function emptyVideoMetadata(): VideoMetadata {
	return {
		title: '',
		species: '',
		cultivar: '',
		genotype: '',
		plant_age: '',
		plant_growth_stage: '',
		growth_environment: '',
		pot_volume: null,
		substrate_type: '',
		special_plant_treatments: '',
		operator: '',
		creation_date: ''
	};
}
