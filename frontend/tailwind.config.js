/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: ["./src/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
  	extend: {
		backgroundImage: {
			logo: "url('/OHCHR.svg')",
		},
  		colors: {
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))',
  			}
  		},
		animation: {
			typing: "typing 1.5s infinite ease-in-out",
		},
		keyframes: {
			typing: {
			"0%": { opacity: "0.2", transform: "translateY(0px)" },
			"50%": { opacity: "1", transform: "translateY(-3px)" },
			"100%": { opacity: "0.2", transform: "translateY(0px)" },
			},
		},
  	}
  },
  plugins: [],
};
