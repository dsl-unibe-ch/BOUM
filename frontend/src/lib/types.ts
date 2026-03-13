export interface ExperimentMetadata {
	title: string;
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
	creation_date: string;
}

export interface ExperimentVideo {
	id: number;
	filename: string;
	status: number;
}

export interface ExperimentUser {
	id: number;
	username: string;
}

export interface ExperimentDetail {
	id: number;
	name: string;
	users: ExperimentUser[];
	videos: ExperimentVideo[];
	metadata: ExperimentMetadata | null;
}

export interface VideoDetail {
	id: number;
	filename: string;
	status: number;
	metadata: ExperimentMetadata | null;
}

export function emptyMetadata(): ExperimentMetadata {
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
