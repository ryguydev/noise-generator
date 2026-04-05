import argparse
from noise_generator.generators import NOISE_TYPES, normalize
from noise_generator.player import play_noise, play_noise_loop
from noise_generator.exporter import EXPORT_FORMATS


def main():
    parser = argparse.ArgumentParser(
        description="Software noise generator — white, pink, brown and more."
    )

    parser.add_argument(
        "--type",
        choices=NOISE_TYPES.keys(),
        default="white",
        help="Type of noise to generate (default: white)"
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=10.0,
        help="Duration in seconds (default: 10)"
    )

    parser.add_argument(
        "--volume",
        type=float,
        default=0.8,
        help="Volume level from 0.0 to 1.0 (default: 0.8)"
    )

    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the noise continuously until Ctrl+C"
    )

    parser.add_argument(
        "--export",
        type=str,
        help="Export to a file instead of playing (e.g. my_noise.wav)"
    )

    parser.add_argument(
        "--format",
        choices=EXPORT_FORMATS.keys(),
        default="wav",
        help="Export format: wav or mp3 (default: wav)"
    )

    parser.add_argument(
        "--sample-rate",
        type=int,
        default=44100,
        help="Sample rate in Hz (default: 44100)"
    )

    parser.add_argument(
        "--fade-out",
        type=float,
        default=1.0,
        help="Fade out duration in seconds (default: 1.0, set to 0 to disable)"
    )

    args = parser.parse_args()

    # Generate the noise
    print(f"Generating {args.type} noise...")
    generator = NOISE_TYPES[args.type]
    signal = generator(args.duration, args.sample_rate)
    signal = normalize(signal, args.volume)

    #Apply fadeout
    if args.fade_out > 0:
        from noise_generator.player import apply_fade_out
        signal = apply_fade_out(signal, args.fade_out)

    # Either export or play
    if args.export:
        exporter = EXPORT_FORMATS[args.format]
        exporter(signal, args.export, args.sample_rate, args.volume)
    elif args.loop:
        play_noise_loop(signal, args.sample_rate, args.volume)
    else:
        play_noise(signal, args.sample_rate, args.volume)


if __name__ == "__main__":
    main()