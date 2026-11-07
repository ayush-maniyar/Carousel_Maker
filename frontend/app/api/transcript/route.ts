import { NextResponse } from "next/server";
import { YoutubeTranscript } from "youtube-transcript";

export async function POST(req: Request) {
  try {
    const { videoUrl } = await req.json();

    if (!videoUrl) {
      return NextResponse.json(
        { error: "A valid YouTube URL is required." },
        { status: 400 }
      );
    }

    // Fetches transcript directly in Node.js runtime mimicking a browser
    const transcript = await YoutubeTranscript.fetchTranscript(videoUrl);

    if (!transcript || transcript.length === 0) {
      return NextResponse.json(
        { error: "No transcript found for this video." },
        { status: 404 }
      );
    }

    const text = transcript.map((t) => t.text).join(" ");

    return NextResponse.json({ text });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Failed to extract YouTube transcript." },
      { status: 500 }
    );
  }
}