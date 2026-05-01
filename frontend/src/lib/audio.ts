const TARGET_SAMPLE_RATE = 16_000; // 16 kHz

export class AudioDecodeError extends Error {
	constructor(message = 'Failed to decode audio data from the selected video file.') {
		super(message);
		this.name = 'AudioDecodeError';
	}
}

/**
 * Extract audio from a video file and return it as a WAV blob.
 * Decodes the video's audio track, downmixes to mono, resamples
 * to 16 kHz, and encodes as PCM 16-bit WAV.
 */
export async function extractAudioFromVideo(file: File): Promise<Blob> {
	const arrayBuffer = await file.arrayBuffer();
	const audioCtx = new AudioContext();

	try {
		let decoded: AudioBuffer;
		try {
			decoded = await audioCtx.decodeAudioData(arrayBuffer);
		} catch {
			throw new AudioDecodeError();
		}

		const mono = downmixToMono(decoded);
		const resampled = await resample(mono, TARGET_SAMPLE_RATE);
		return encodeWav(resampled);
	} finally {
		await audioCtx.close();
	}
}

/** Mix all channels down to a single mono channel. */
function downmixToMono(buffer: AudioBuffer): AudioBuffer {
	if (buffer.numberOfChannels === 1) return buffer;

	const length = buffer.length;
	const mono = new Float32Array(length);
	const numChannels = buffer.numberOfChannels;

	for (let ch = 0; ch < numChannels; ch++) {
		const channel = buffer.getChannelData(ch);
		for (let i = 0; i < length; i++) {
			mono[i] += channel[i] / numChannels;
		}
	}

	const ctx = new OfflineAudioContext(1, length, buffer.sampleRate);
	const out = ctx.createBuffer(1, length, buffer.sampleRate);
	out.getChannelData(0).set(mono);
	return out;
}

/** Resample an AudioBuffer to a target sample rate using OfflineAudioContext. */
async function resample(buffer: AudioBuffer, targetRate: number): Promise<AudioBuffer> {
	if (buffer.sampleRate === targetRate) return buffer;

	const duration = buffer.duration;
	const targetLength = Math.ceil(duration * targetRate);
	const offline = new OfflineAudioContext(1, targetLength, targetRate);

	const source = offline.createBufferSource();
	source.buffer = buffer;
	source.connect(offline.destination);
	source.start(0);

	return offline.startRendering();
}

function encodeWav(buffer: AudioBuffer): Blob {
	const numChannels = buffer.numberOfChannels;
	const sampleRate = buffer.sampleRate;
	const bitsPerSample = 16;
	const bytesPerSample = bitsPerSample / 8;
	const blockAlign = numChannels * bytesPerSample;
	const numSamples = buffer.length;
	const dataSize = numSamples * blockAlign;
	const headerSize = 44;

	const out = new ArrayBuffer(headerSize + dataSize);
	const view = new DataView(out);

	writeString(view, 0, 'RIFF');
	view.setUint32(4, headerSize - 8 + dataSize, true);
	writeString(view, 8, 'WAVE');

	writeString(view, 12, 'fmt ');
	view.setUint32(16, 16, true);
	view.setUint16(20, 1, true); // PCM
	view.setUint16(22, numChannels, true);
	view.setUint32(24, sampleRate, true);
	view.setUint32(28, sampleRate * blockAlign, true);
	view.setUint16(32, blockAlign, true);
	view.setUint16(34, bitsPerSample, true);

	writeString(view, 36, 'data');
	view.setUint32(40, dataSize, true);

	const channels: Float32Array[] = [];
	for (let ch = 0; ch < numChannels; ch++) {
		channels.push(buffer.getChannelData(ch));
	}

	let offset = headerSize;
	for (let i = 0; i < numSamples; i++) {
		for (let ch = 0; ch < numChannels; ch++) {
			const sample = Math.max(-1, Math.min(1, channels[ch][i]));
			view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
			offset += bytesPerSample;
		}
	}

	return new Blob([out], { type: 'audio/wav' });
}

function writeString(view: DataView, offset: number, str: string): void {
	for (let i = 0; i < str.length; i++) {
		view.setUint8(offset + i, str.charCodeAt(i));
	}
}
