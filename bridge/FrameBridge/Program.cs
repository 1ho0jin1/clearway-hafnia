// FrameBridge: streams live frames from XProtect cameras to stdout at the camera's full frame rate.
//
// The REST task JpegGetLive only returns keyframes (1 per second on our cameras), too few for tracking. This app uses
// the MIP .NET library's JPEGLiveSource instead, following Milestone's CameraStreamResolution component sample.
//
//   FrameBridge.exe [--server http://localhost] [--width 0] <camera name> [<camera name> ...]
//
// Logs in as the current Windows user (no password). Each frame is one binary record on stdout, little-endian:
//   int32 camera index (order of the names given) | int64 frame time, Unix ms UTC | int32 JPEG length | JPEG bytes
// Log lines go to stderr. The process runs until stdin closes or it is killed.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using VideoOS.Platform;
using VideoOS.Platform.Live;
using VideoOS.Platform.Login;

namespace FrameBridge
{
    internal static class Program
    {
        private static readonly Guid IntegrationId = new Guid("5D1C8E57-2C43-4E1B-9F0E-7E3A1B6C4D21");
        private static readonly object StdoutLock = new object();
        private static Stream _stdout;

        private static int Main(string[] args)
        {
            string server = "http://localhost";
            int width = 0;
            var names = new List<string>();
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--server") server = args[++i];
                else if (args[i] == "--width") width = int.Parse(args[++i]);
                else names.Add(args[i]);
            }
            if (names.Count == 0)
            {
                Log("usage: FrameBridge.exe [--server http://localhost] [--width 0] <camera name> ...");
                return 2;
            }

            VideoOS.Platform.SDK.Environment.Initialize();
            VideoOS.Platform.SDK.Media.Environment.Initialize();

            // The machine uses plain HTTP: secureOnly false. Empty user + Negotiate = the current Windows user.
            Uri uri = new UriBuilder(server).Uri;
            CredentialCache cc = Util.BuildCredentialCache(uri, "", "", "Negotiate");
            VideoOS.Platform.SDK.Environment.AddServer(false, uri, cc);
            try
            {
                VideoOS.Platform.SDK.Environment.Login(uri, IntegrationId, "Hackathon FrameBridge", "1.0", "hafnia-hackathon-2026");
            }
            catch (Exception ex)
            {
                Log("login failed: " + ex.Message);
                return 1;
            }
            if (LoginSettingsCache.GetLoginSettings(uri.DnsSafeHost) == null)
            {
                Log("login failed: no login settings");
                return 1;
            }

            List<Item> cameras = AllCameras();
            _stdout = Console.OpenStandardOutput();
            var sources = new List<JPEGLiveSource>();
            for (int index = 0; index < names.Count; index++)
            {
                Item camera = cameras.FirstOrDefault(c => string.Equals(c.Name, names[index], StringComparison.OrdinalIgnoreCase));
                if (camera == null)
                {
                    Log($"camera not found: {names[index]}");
                    return 1;
                }
                int cameraIndex = index;
                var source = new JPEGLiveSource(camera) { LiveModeStart = true, Width = width, Height = 0, KeyFramesOnly = false };
                source.Init();
                source.LiveContentEvent += (sender, e) => OnFrame(cameraIndex, e as LiveContentEventArgs);
                sources.Add(source);
                Log($"streaming [{cameraIndex}] {camera.Name}");
            }

            // Run until the reading process closes our stdin (or kills us).
            Console.In.ReadToEnd();
            foreach (var s in sources) s.Close();
            return 0;
        }

        private static void OnFrame(int cameraIndex, LiveContentEventArgs args)
        {
            if (args == null) return;
            if (args.Exception != null)
            {
                Log($"[{cameraIndex}] live error: {args.Exception.Message}");
                return;
            }
            if (args.LiveContent == null) return;
            try
            {
                byte[] jpeg = args.LiveContent.Content;
                long ms = new DateTimeOffset(DateTime.SpecifyKind(args.LiveContent.BeginTime.ToUniversalTime(), DateTimeKind.Utc)).ToUnixTimeMilliseconds();
                lock (StdoutLock)
                {
                    _stdout.Write(BitConverter.GetBytes(cameraIndex), 0, 4);
                    _stdout.Write(BitConverter.GetBytes(ms), 0, 8);
                    _stdout.Write(BitConverter.GetBytes(jpeg.Length), 0, 4);
                    _stdout.Write(jpeg, 0, jpeg.Length);
                    _stdout.Flush();
                }
            }
            catch (IOException)
            {
                Environment.Exit(0);   // the reader went away
            }
            finally
            {
                args.LiveContent.Dispose();
            }
        }

        private static List<Item> AllCameras()
        {
            var found = new List<Item>();
            void Walk(Item parent)
            {
                foreach (Item item in parent.GetChildren() ?? new List<Item>())
                {
                    if (item.FQID.Kind == Kind.Camera && item.FQID.FolderType == FolderType.No) found.Add(item);
                    else if (item.HasChildren != HasChildren.No) Walk(item);
                }
            }
            foreach (Item root in Configuration.Instance.GetItemsByKind(Kind.Camera)) Walk(root);
            return found;
        }

        private static void Log(string message) => Console.Error.WriteLine($"{DateTime.UtcNow:HH:mm:ss.fff} {message}");
    }
}
