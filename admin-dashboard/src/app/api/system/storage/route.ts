import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

async function getDirectorySize(target: string): Promise<number> {
  try {
    const entries = await fs.readdir(target, { withFileTypes: true });
    const sizes = await Promise.all(
      entries.map(async (entry) => {
        const full = path.join(target, entry.name);
        try {
          if (entry.isDirectory()) return await getDirectorySize(full);
          const stat = await fs.stat(full);
          return stat.size;
        } catch {
          return 0;
        }
      }),
    );
    return sizes.reduce((a, b) => a + b, 0);
  } catch {
    return 0;
  }
}

export async function GET() {
  const videosDir = process.env.VIDEOS_DIR || "/app/videos";
  const imagesDir = process.env.IMAGES_DIR || "/app/images";

  const [videosBytes, imagesBytes] = await Promise.all([
    getDirectorySize(videosDir),
    getDirectorySize(imagesDir),
  ]);

  let totalBytes = 0;
  let freeBytes = 0;
  try {
    // statfs gives filesystem totals for the mount that holds the videos folder
    const stat = await fs.statfs(videosDir);
    totalBytes = stat.bsize * stat.blocks;
    freeBytes = stat.bsize * stat.bfree;
  } catch {
    // Fallback: derive total from app mount if statfs fails
    try {
      const stat = await fs.statfs("/");
      totalBytes = stat.bsize * stat.blocks;
      freeBytes = stat.bsize * stat.bfree;
    } catch {
      totalBytes = videosBytes + imagesBytes;
      freeBytes = 0;
    }
  }

  const payload = {
    videos_bytes: videosBytes,
    images_bytes: imagesBytes,
    system_bytes: 0,
    used_bytes: videosBytes + imagesBytes,
    total_bytes: totalBytes,
    free_bytes: freeBytes,
  };

  return NextResponse.json(payload);
}
