from manim import *

# ── Brand: gold-on-void (C:\æ AGENTS.md) ──────────────────────────────
VOID   = "#050505"
GOLD   = "#D4AF37"
GOLD_D = "#8A6D1F"
SILVER = "#E8E2C8"
MONO   = "Consolas"

class AEIntro(Scene):
    def setup(self):
        self.camera.background_color = VOID

    def scanlines(self):
        lines = VGroup()
        for y in np.arange(-3.4, 3.4, 0.18):
            ln = Line([-7, y, 0], [7, y, 0], stroke_width=0.6,
                      color=GOLD, stroke_opacity=0.045)
            lines.add(ln)
        return lines

    def construct(self):
        # ── 0.0–2.0s : void boot, prompt types, cursor blinks ────────
        self.play(FadeIn(self.scanlines(), run_time=0.8))
        prompt = Text(">_æ:", font=MONO, font_size=50, color=GOLD, weight=BOLD)
        prompt.move_to(LEFT*2.2 + UP*1.4)
        self.play(Write(prompt, run_time=1.4))
        cursor = Rectangle(width=0.32, height=0.6, fill_color=GOLD,
                           fill_opacity=1, stroke_opacity=0).next_to(prompt, RIGHT, buff=0.04)
        self.play(FadeIn(cursor, run_time=0.15))
        self.wait(0.25)
        self.play(FadeOut(cursor, run_time=0.15))

        # ── 2.0–4.5s : æ:// resolves big (clean swap, no ghost) ───────
        ae = Text("æ://", font=MONO, font_size=116, color=GOLD, weight=BOLD)
        ae.move_to(ORIGIN)
        self.play(ReplacementTransform(prompt, ae, run_time=1.1))
        self.play(ae.animate.scale(1.07), rate_func=there_and_back, run_time=0.7)
        self.wait(0.35)

        # ── 4.5–8.0s : scheme dispatcher blooms (BRIGHT gold nodes) ───
        schemes = ["+bæsic://", "pc://mesh/victus/local", "rtx3050://",
                   "+æ://secrets", "cuda_IDE_RTX", "+æ://cc"]
        nodes = VGroup()
        for i, s in enumerate(schemes):
            ang = TAU * i / len(schemes) - PI/2
            t = Text(s, font=MONO, font_size=25, color=GOLD)
            t.move_to(np.array([2.7*np.cos(ang), 2.3*np.sin(ang), 0]))
            nodes.add(t)
        hub = Dot(ae.get_center(), radius=0.13, color=GOLD)
        self.play(FadeIn(hub, run_time=0.2))
        self.play(LaggedStart(*[FadeIn(n, run_time=0.45) for n in nodes], lag_ratio=0.1))
        spokes = VGroup()
        for n in nodes:
            ln = Line(hub.get_center(), n.get_center(), stroke_color=GOLD,
                      stroke_opacity=0.55, stroke_width=1.8)
            spokes.add(ln)
        self.play(*[Create(sp, run_time=0.45) for sp in spokes])
        self.wait(0.4)
        self.play(Rotate(VGroup(nodes, spokes), angle=0.16, about_point=ORIGIN, run_time=0.7))
        self.wait(0.2)

        # ── 8.0–10.0s : collapse into thesis ─────────────────────────
        self.play(FadeOut(VGroup(nodes, spokes, hub), run_time=0.45),
                  ae.animate.move_to(UP*1.0).scale(0.72))
        thesis = Text("language is compute", font=MONO, font_size=44, color=GOLD, weight=BOLD)
        thesis.next_to(ae, DOWN, buff=0.5)
        self.play(Write(thesis, run_time=1.2))
        self.wait(0.35)

        # ── 10.0–12.0s : tags lock in + hold ─────────────────────────
        tags = Text("#opensourceware   #hermiphicationisinevitable",
                    font=MONO, font_size=21, color=GOLD_D)
        tags.next_to(thesis, DOWN, buff=0.45)
        self.play(FadeIn(tags, run_time=0.7))
        self.play(ae.animate.scale(1.05), rate_func=there_and_back, run_time=0.5)
        self.wait(1.1)
