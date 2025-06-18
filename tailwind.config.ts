module.exports = {
	content: [
		"./src/**/*.{html,js,ts,jsx,tsx}",
		"app/**/*.{ts,tsx}",
		"components/**/*.{ts,tsx}",
	],
	theme: {
		extend: {
			colors: {
				absolutewhite: "var(--absolutewhite)",
				"dark-10": "var(--dark-10)",
				"dark-20": "var(--dark-20)",
				"dark-24": "var(--dark-24)",
				"foundation-blackb200": "var(--foundation-blackb200)",
				"foundation-blackblack-1": "var(--foundation-blackblack-1)",
				"foundation-blackblack-100": "var(--foundation-blackblack-100)",
				"foundation-blackblack-400": "var(--foundation-blackblack-400)",
				"foundation-blackblack-500": "var(--foundation-blackblack-500)",
				"foundation-blackblack-6": "var(--foundation-blackblack-6)",
				"foundation-blackblack-9": "var(--foundation-blackblack-9)",
				"foundation-blueblue-100": "var(--foundation-blueblue-100)",
				"foundation-blueblue-300": "var(--foundation-blueblue-300)",
				"foundation-blueblue-400": "var(--foundation-blueblue-400)",
				"foundation-blueblue-50": "var(--foundation-blueblue-50)",
				"foundation-blueblue-500": "var(--foundation-blueblue-500)",
				"foundation-blueblue-600": "var(--foundation-blueblue-600)",
				"foundation-blueblue-700": "var(--foundation-blueblue-700)",
				"foundation-blueblue-900": "var(--foundation-blueblue-900)",
				"foundation-greyg300": "var(--foundation-greyg300)",
				"foundation-whitewhite-300": "var(--foundation-whitewhite-300)",
				"foundation-whitewhite-50": "var(--foundation-whitewhite-50)",
				"foundation-whitewhite-500": "var(--foundation-whitewhite-500)",
				"foundation-whitewhite-800": "var(--foundation-whitewhite-800)",
				"foundation-whitewhite-900": "var(--foundation-whitewhite-900)",
				"light-90": "var(--light-90)",
				"light-blue90": "var(--light-blue90)",
				border: "hsl(var(--border))",
				input: "hsl(var(--input))",
				ring: "hsl(var(--ring))",
				background: "hsl(var(--background))",
				foreground: "hsl(var(--foreground))",
				primary: {
					DEFAULT: "hsl(var(--primary))",
					foreground: "hsl(var(--primary-foreground))",
				},
				secondary: {
					DEFAULT: "hsl(var(--secondary))",
					foreground: "hsl(var(--secondary-foreground))",
				},
				destructive: {
					DEFAULT: "hsl(var(--destructive))",
					foreground: "hsl(var(--destructive-foreground))",
				},
				muted: {
					DEFAULT: "hsl(var(--muted))",
					foreground: "hsl(var(--muted-foreground))",
				},
				accent: {
					DEFAULT: "hsl(var(--accent))",
					foreground: "hsl(var(--accent-foreground))",
				},
				popover: {
					DEFAULT: "hsl(var(--popover))",
					foreground: "hsl(var(--popover-foreground))",
				},
				card: {
					DEFAULT: "hsl(var(--card))",
					foreground: "hsl(var(--card-foreground))",
				},
			},
			fontFamily: {
				bricolage: ['"Bricolage Grotesque"', 'sans-serif'],
			},
			boxShadow: { "drop-shadow-200": "var(--drop-shadow-200)" },
			borderRadius: {
				lg: "var(--radius)",
				md: "calc(var(--radius) - 2px)",
				sm: "calc(var(--radius) - 4px)",
			},
			keyframes: {
				"accordion-down": {
					from: { height: "0" },
					to: { height: "var(--radix-accordion-content-height)" },
				},
				"accordion-up": {
					from: { height: "var(--radix-accordion-content-height)" },
					to: { height: "0" },
				},
			},
			animation: {
				"accordion-down": "accordion-down 0.2s ease-out",
				"accordion-up": "accordion-up 0.2s ease-out",
			},
		},
		container: { center: true, padding: "2rem", screens: { "2xl": "1400px" } },
	},
	plugins: [],
	darkMode: ["class"],
};
