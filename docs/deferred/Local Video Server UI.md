# Local Video Server UI

A video player can be designed with glassmorphism (frosted glass, transparency, and blur) or neumorphism (soft shadows, embossed look, and subtle depth) or even a combination of both. Both design styles offer unique visual appeal, with glassmorphism creating a modern, layered depth and neumorphism providing a more tactile, three-dimensional feel. You can find examples and tutorials for creating such video players on design platforms like Dribbble and YouTube, and see their implementation in popular operating systems like macOS and Windows 11.

## **Glassmorphism Video Player**

Appearance:  
Elements have a frosted glass effect, appearing translucent and blurred, layered over a background image or color.

Key Features:  
Creates a sense of depth through layers, transparency, and subtle light and shadow effects.

Examples:  
Prominent in modern operating systems like macOS Big Sur and Windows 11, which use blurred and translucent elements for a sleek look.
How to Create:  
Achieved by decreasing the opacity of elements, adding a background blur, rounding corners, and using subtle borders and shadows to create the "glass" effect.

![][image1]

## **Characteristics of Glassmorphism**

Two main characteristics create glassmorphism’s translucency: opacity and background blur. To achieve a glassmorphic effect, designers can vary the opacity and background blur of components to affect how much background information is visible and distinguishable. Designers can also opt to use strokes and gradients for more depth and contrast if the glassmorphic elements will be placed on both complex and simple backgrounds.

## **Opacity**

To achieve a glassmorphic look, you need to be able to see through the element you are designing. You can achieve this by adjusting the opacity of your component’s fill (the color, pattern, or gradient inside of an object).
Opacity defines how much you can see through an element. The more opaque an element is, the less you can see the contents behind it. The less opaque, the more you can see. For example, the glass windows in your home probably have 0% opacity, meaning you can see everything outside clearly.

![][image2]

## **Background Blur**

Background blur distorts objects behind the main component, giving background elements a fuzzy, out-of-focus appearance. Examples of background blur in the physical world are a walk-in shower with a frosted glass door or a conference room with privacy glass. You can still see objects on the other side, but they are blurred to a point where you might be unable to identify them.

Background blur provides this same effect for low-opacity digital elements. For instance, a white rectangle with 30% opacity and a 25-pixel blur will distort background elements but still have somewhat distinguishable edges. However, by adjusting the blur to 100 pixels, those same background elements become more out-of-focus and blend together.

![][image3]

## **Strokes and Gradients**

In addition to opacity and background blur, strokes (borders) and gradients can emphasize depth of glassmorphic elements, especially when these elements are placed on simple or one-color backgrounds.
A gradient takes two or more colors, color shades, or color opacities and blends them together seamlessly. Gradients can be applied to both fills and strokes of an element. You can add a low-opacity or gradient stroke around a component to create an illusion of thickness. Gradients can also be applied to the fill of the component to mimic the reflection of light on actual glass.

![][image4]

## **Designing with Glassmorphism: Best Practices**

When incorporating glass-like materials in your UI, it is essential to understand the accessibility constraints of translucent components. One of the most significant issues with glassmorphism stems from text readability problems, with text either being too light or too dark or backgrounds being too busy. Follow these three best practices when incorporating glass-like materials into your design system

## **Meet Contrast Requirements**

Ensure that text and graphical elements meet contrast requirements. Since glassmorphic components are translucent, textual elements can fall over multiple colors, which can affect readability. For instance, if you are designing a card component over a busy background, your text might only have enough contrast over certain areas and be challenging to read. If you are designing in Figma, I recommend checking out the plugin Contrast by Willowtree, which lets you quickly check the contrast ratios of text and other design elements.

## **More Blur Is Better**

More background blur is better, especially with intricate backgrounds (e.g., video, photography, animations). Many UI designs on Behance or Dribble try too hard to keep background elements distinguishable. However, overwhelming backgrounds can make it hard for users to focus on meaningful content and affect text readability.

Background blur provides this same effect for low-opacity digital elements. For instance, a white rectangle with 30% opacity and a 25-pixel blur will distort background elements but still have somewhat distinguishable edges. However, by adjusting the blur to 100 pixels, those same background elements become more out-of-focus and blend together.

![][image4]

## **Let Users Adjust Transparency**

If feasible, give users the option to control contrast or transparency settings. For example, Apple’s accessibility features allow users to reduce transparency or increase contrast, minimizing or removing the blur of glassmorphic components altogether. These options enable the interface to be adaptable for low-vision users.

# glassmorphism and neumorphism video player

To design a video player using both glassmorphism and neumorphism, you can create a hybrid interface that leverages the strengths of both styles. This approach combines neumorphism's soft, tactile controls with glassmorphism's layered, depth-creating panels for a modern and immersive look.

**The combined concept**

- [ ] Neumorphic base: Use a soft, subtle neumorphic background for the main video player container. The controls (like play, pause, volume, and progress bar) are soft, extruded elements that appear to be part of the surface.  
- [ ] Glassmorphic display: The video itself would be presented within a translucent, frosted-glass frame. This creates a distinct layering effect, with the video content floating above a dynamic, blurred background.  
- [ ] A cohesive aesthetic: By blending these two trends, you get a clean, minimal interface that feels both futuristic and approachable.

**Design elements and features**

Neumorphic controls

- [ ] Play/pause button: A prominent, circular or square button that appears to be gently raised from the interface surface. A subtle inner shadow can be used to show a "pressed" state when the user interacts with it.  
- [ ] Progress bar: A track with soft, embedded divots to create a subtle 3D channel. The scrubber handle is a raised, circular neumorphic element that stands out slightly.  
- [ ] Volume controls: A slider bar with the same embedded track effect, and a raised, tactile-looking handle for adjustment.  
- [ ] Other options: Buttons for fullscreen, settings, and other features can also be styled with the embedded neumorphic effect.

Glassmorphic layers

- [ ] Main display window: The video feed is bordered by a semi-transparent, frosted-glass panel. The background behind the player—a dynamic gradient, album artwork, or the user's desktop—is visible but blurred, adding depth and focusing the user's attention on the video.  
- [ ] Overlays: Any additional information, like video title or a channel logo, can appear on a smaller, dedicated glassmorphic panel in a corner of the screen.  
- [ ] Dynamic effects: Hovering over the glassmorphic video window could increase the blur slightly or add a subtle light reflection, enhancing the realistic glass effect.

How the two styles work together

| Feature  | Neumorphism | Glassmorphism |
| :---- | :---- | :---- |
| Feel | Soft, extruded, and tactile | Layered, transparent, and ethereal |
| Use case | Control elements like buttons, sliders, and toggles | Container elements and background panels for content display |
| Key visual | Monochromatic elements that appear to protrude from or recede into the background using subtle, soft shadows | Translucent panels with a blurred background, creating a floating glass effect |
| Effect on video player | Provides a clean, modern aesthetic for the functional parts of the interface, like controls | Creates a sense of depth and a high-tech visual flair for the video display and information panels |

Creating accessible designs with a blend of glassmorphism and neumorphism requires careful consideration of contrast, readability, and visual hierarchy. Both styles can present accessibility challenges, but with the right practices, you can create a hybrid interface that is both visually engaging and usable for everyone.

## **Best practices for glassmorphism**

### Prioritize contrast and legibility

- [ ] Meet WCAG contrast minimums: Ensure all text and essential UI elements, like icons, meet or exceed the contrast minimums outlined in the Web Content Accessibility Guidelines (WCAG).  
- [ ] Use background overlays: Place a semi-opaque or solid fill behind text to separate it from the constantly shifting, blurred background. Do not rely solely on the blur effect to provide contrast.  
- [ ] Control blur intensity: Avoid using excessive blur values, which can obscure the background and make text harder to read. A slight, subtle blur is often sufficient to achieve the desired effect.

### Offer reduced transparency options

- [ ] Respect user preferences: Use the prefers-reduced-transparency media query to detect if a user has enabled a setting to reduce transparency in their operating system.  
- [ ] Provide a toggle: Allow users to disable or reduce the glassmorphic effects directly in your application's settings, replacing the elements with a solid, opaque background for better readability.

## **Best practices for neumorphism**

### Increase contrast beyond typical designs

- [ ] Choose colors carefully: Traditional neumorphic designs, with their low contrast, often fail WCAG standards. To fix this, use a muted color palette but choose a background color different enough from your elements to provide sufficient contrast.  
- [ ] Boost icon and text contrast: Ensure the text and icons on your neumorphic controls have a contrast ratio of at least 4.5:1 against their button's color. Interactive elements should maintain a contrast of 3:1.

### Ensure all interactive elements are obvious

- [ ] Design clear states: All interactive elements need clear visual cues for their default, hover, active, and focus states.  
- [ ] Focus states: Crucial for keyboard navigation, use a strong box-shadow, solid outline, or color change on focus to highlight the active element.  
- [ ] Hover states: A subtle increase in elevation or a change in the element's inner shadow can indicate that it is interactive.  
- [ ] Use additional cues: Given the subtle nature of neumorphism, pair icons with clear text labels to avoid ambiguity and ensure all users understand an element's purpose.

## **Combining the two styles effectively**

### Maintain consistency

- [ ] Follow WCAG guidelines rigorously: The combination of transparency and subtle shadows increases the risk of accessibility issues. Adhere to WCAG standards for all interactive elements and text.  
- [ ] Create a robust component library: Document your color palettes, elevation shadows, and border treatments to ensure consistent contrast and visual hierarchy across your entire interface.
- [ ] Test with assistive technologies
- [ ] Use screen readers: Perform testing with screen readers like JAWS, NVDA, and VoiceOver to ensure your components are properly identified and understandable.
- [ ] Use contrast analyzers: Use tools like the WebAIM Contrast Checker to verify that your color combinations meet accessibility standards.

### Test with assistive technologies

- [ ] Use screen readers: Perform testing with screen readers like JAWS, NVDA, and VoiceOver to ensure your components are properly identified and understandable.  
- [ ] Check with contrast analyzers: Use tools like the WebAIM Contrast Checker to verify that your color combinations meet accessibility standards.  
- [ ] Enable high-contrast mode: Test how your interface behaves in Windows High Contrast Mode or equivalent system-level settings. Many design effects will be stripped away, so ensure the interface remains usable.

Designing a local video server UI using glassmorphism and neumorphism creates a modern, immersive, and tactile experience, and the two styles can be combined to balance visual flair with usability. Both trends leverage shadows, transparency, and depth to enhance the user experience in distinct ways.
Design strategy: Combining glassmorphism and neumorphism

- [ ] Combine for visual hierarchy: Use glassmorphism for background elements and neumorphism for interactive controls. The floating, semi-transparent layers of glassmorphism can be used for main viewing panels and sidebars, while the soft, tactile buttons of neumorphism can be used for playback controls, settings, and other key actions.  
- [ ] Establish a consistent light source: For a cohesive look, use a single, consistent light source to define all shadows and highlights. This ensures that all neumorphic elements appear to be illuminated from the same direction, which prevents the interface from looking cluttered or mismatched.  
- [ ] Use a dark theme: Dark mode is an ideal canvas for both design styles. The transparent layers of glassmorphism stand out against the deep background, and neumorphic shadows are more pronounced, giving the interface a high-end, immersive feel perfect for a media server.  
- [ ] Emphasize key elements: Use more pronounced glassmorphic or neumorphic effects for calls to action or to draw attention to important information. For example, a playback window could have a stronger glass effect than a settings sidebar, and a "Play" button could have a more defined neumorphic push-in state.  
- [ ] Use color sparingly: Both styles typically use a minimalist or monochromatic color palette. Introduce pops of vibrant or pastel colors in the background for glassmorphism to catch the eye, but keep neumorphic elements in soft, muted tones.

Applying glassmorphism  
Elements and applications

- [ ] Main video player: Use a subtle glassmorphic overlay on the video player itself. It can dim slightly when playback is paused or when an on-screen overlay appears.  
- [ ] Sidebars and navigation: Use transparent, frosted-glass panels for left or top navigation bars that float over the video content, allowing the content of the dashboard to scroll underneath it.  
- [ ] Overlays and pop-ups: Information overlays (e.g., video details, file information) or modal windows can appear as frosted-glass cards, keeping the user focused on the content while maintaining context.

Best practices for glassmorphism

- [ ] Ensure readability: Always ensure text and icons have enough contrast with the background, even with varying images or video playing behind them.  
- [ ] Use subtle gradients and strokes: Add a slight gradient to the glassmorphic element's fill and a light, semi-transparent stroke to give it a more realistic, glass-like edge.  
- [ ] Control performance: Be mindful of how many blur effects you apply, as excessive blurring can impact performance, especially on older devices.

Applying neumorphism  
Elements and applications

- [ ] Playback controls: Use neumorphic buttons for play/pause, volume sliders, and seek bars. These elements should appear to extrude from the background and create a sunken effect when pressed, giving a satisfying tactile feel.  
- [ ] Dashboard cards: For a server statistics or user dashboard, design each card with soft, embossed edges so it appears to be physically part of the background.  
- [ ] Toggles and switches: Use neumorphic on/off toggles for settings such as subtitles or audio tracks. The switch can look like a physical component that pushes in and out of the surface.

Best practices for neumorphism

- [ ] Use for key interactions: Apply neumorphism selectively to interactive elements where it adds a tangible feel. Overuse can make the interface feel noisy.  
- [ ] Prioritize accessibility: The low contrast common in neumorphism can create accessibility issues. Add sufficient color contrast or provide a fallback design for users with visual impairments.  
- [ ] Define button states clearly: Clearly define the visual state of buttons (e.g., active, hover, pressed) using shadow manipulation to indicate interactivity.

- [ ] Glassmorphic controls: Playback controls appear as a transparent, frosted-glass overlay that fades in when the user moves their mouse. The blur effect prevents them from obscuring the video.  
- [ ] Neumorphic elements: Within the glassmorphic overlay, the individual buttons (e.g., Play, Pause, Next Episode) are neumorphic, offering a tactile feel. A volume slider also uses the soft, embossed style of neumorphism.

Dashboard view

- [ ] Monochromatic background: The primary dashboard uses a soft, dark gray or charcoal background.  
- [ ] Neumorphic cards: Content cards for recently added movies, server health, or user activity are soft, embossed rectangles that appear to rise subtly from the background.  
- [ ] Glassmorphic sidebar: A vertical, frosted-glass sidebar for main navigation (e.g., Movies, TV Shows, Settings) is fixed to the left, allowing the content of the dashboard to scroll underneath it.  
- [ ] Neumorphic search bar: The search bar at the top is a recessed neumorphic element that looks like an indentation in the surface.

Mobile/small screen view

- [ ] Adapt glassmorphism for overlays: As mobile screens are smaller, use glassmorphic layers primarily for full-screen menu overlays to avoid clutter.  
- [ ] Use neumorphism for tabs: A navigation bar at the bottom of the screen can use neumorphic-style tabs. When a user selects a tab, its icon and background could switch to a sunken, pressed state, indicating it is active.

By thoughtfully blending these two design styles, a local video server UI can be both visually stunning and highly functional, providing an intuitive, premium, and tactile user experience.  
![][image5]
