from manim import *

# ── Omniverse-direction æ:// intro — 3D neural mesh, RTX-grade gold-on-void ──
# Rendered on local Victus RTX 3050 (sovereign silicon, not NVIDIA cloud).
VOID   = "#050505"
GOLD   = "#D4AF37"
GOLD_D = "#8A6D1F"
SILVER = "#E8E2C8"
MONO   = "Consolas"

class AEOmniverse(ThreeDScene):
    def setup(self):
        self.camera.background_color = VOID
        self.set_camera_orientation(phi=68*DEGREES, theta=-30*DEGREES, distance=14)

    def scanlines(self):
        g = VGroup()
        for y in np.arange(-4, 4, 0.2):
            g.add(Line([-8, y, 0], [8, y, 0], stroke_width=0.5,
                        color=GOLD, stroke_opacity=0.04))
        return g

    def mktext(self, s, size, color=GOLD):
        return Text(s, font=MONO, font_size=size, color=color, weight=BOLD)

    def smiley(self, r=0.22):
        # font-independent render of the operator glyph ☺ (U+263A)
        g = VGroup()
        g.add(Circle(r, color=GOLD, fill_opacity=0, stroke_width=2.5))
        g.add(Dot(LEFT*0.32*r + UP*0.18*r, radius=0.05, color=GOLD))
        g.add(Dot(RIGHT*0.32*r + UP*0.18*r, radius=0.05, color=GOLD))
        g.add(ArcBetweenPoints(LEFT*0.4*r + DOWN*0.12*r,
                               RIGHT*0.4*r + DOWN*0.12*r, angle=-PI/2.2,
                               color=GOLD, stroke_width=2.5))
        return g

    def glyph_label(self, s, size):
        # if s carries the ☺ operator glyph, draw it as a shape + text tail
        if s.startswith("\u263a"):
            tail = self.mktext(s[1:], size, GOLD)
            sm = self.smiley(0.2)
            grp = VGroup(sm, tail).arrange(RIGHT, buff=0.06)
            return grp
        return self.mktext(s, size, GOLD)

    def construct(self):
        # ── 0-2.2s : void boot, prompt types (3D) ──────────────────
        self.add(self.scanlines())
        prompt = self.mktext(">_æ:", 44).move_to(LEFT*2.4 + UP*1.6)
        self.play(Write(prompt, run_time=1.4))
        cur = Rectangle(width=0.28, height=0.52, color=GOLD, fill_opacity=1,
                        stroke_opacity=0).next_to(prompt, RIGHT, buff=0.03)
        self.play(FadeIn(cur, run_time=0.15)); self.wait(0.25)
        self.play(FadeOut(cur, run_time=0.15))

        # ── 2.2-4.5s : æ:// resolves, camera pushes in ──────────────
        ae = self.mktext("æ://", 104).move_to(ORIGIN)
        self.play(ReplacementTransform(prompt, ae, run_time=1.1))
        self.move_camera(phi=70*DEGREES, theta=-20*DEGREES, distance=11, run_time=1.0)
        self.wait(0.3)

        # ── 4.5-8.5s : 3D neural mesh blooms + orbits (omniverse feel, ALIVE) ─
        schemes = ["+bæsic://", "pc://mesh/victus/local", "rtx3050://",
                   "+æ://secrets", "cuda_IDE_RTX", "+æ://cc", "☺://cc"]
        core = Dot(ORIGIN, radius=0.18, color=GOLD)
        nodes, edges = VGroup(), VGroup()
        labels = VGroup()
        for i, s in enumerate(schemes):
            ang = TAU*i/len(schemes)
            p = np.array([3.0*np.cos(ang), 1.6*np.sin(ang), 1.4*np.sin(ang*1.3)])
            d = Dot(p, radius=0.1, color=GOLD)
            nodes.add(d)
            edges.add(Line(core.get_center(), p, stroke_color=GOLD,
                            stroke_opacity=0.5, stroke_width=1.6))
            lb = self.glyph_label(s, 22).move_to(p + OUT*0.3)
            labels.add(lb)
        mesh = VGroup(core, nodes, edges, labels)
        self.play(FadeIn(core, run_time=0.2))
        self.play(LaggedStart(*[FadeIn(n, run_time=0.4) for n in nodes],
                              lag_ratio=0.1),
                  LaggedStart(*[Create(e, run_time=0.4) for e in edges],
                              lag_ratio=0.1),
                  LaggedStart(*[FadeIn(l, run_time=0.4) for l in labels],
                              lag_ratio=0.1))
        # ALIVE: continuous orbit + node pulse + slow camera drift (not archived)
        mesh.add_updater(lambda m, dt: m.rotate(0.35*dt, about_point=ORIGIN))
        nodes.add_updater(lambda g, dt: g.set_opacity(0.6 + 0.4*np.sin(self.time*3)))
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(2.2)
        self.stop_ambient_camera_rotation()
        mesh.clear_updaters()
        nodes.clear_updaters()

        # ── 8.5-10.5s : collapse to thesis (camera front-on for 2D text) ──
        self.move_camera(phi=0*DEGREES, theta=-90*DEGREES, distance=12, run_time=0.6)
        self.play(FadeOut(VGroup(nodes, edges, labels), run_time=0.4),
                  ae.animate.move_to(UP*1.1).scale(0.72))
        thesis = self.mktext("æ:// language is compute", 38).next_to(ae, DOWN, buff=0.5)
        self.play(Write(thesis, run_time=1.2))
        self.wait(0.3)

        # ── 10.5-12s : end-card — operator glyph + real brand tags ──
        cc = self.glyph_label("\u263a://cc  — command & control", 20)
        cc.next_to(thesis, DOWN, buff=0.4)
        tags = self.mktext(
            "#attentionisallyouneed #allyouneedisattention #startabusiness "
            "#daollc #clillc #llmstore #neuromitosis", 15, GOLD_D)
        tags.next_to(cc, DOWN, buff=0.25)
        self.play(FadeIn(cc, run_time=0.6), FadeIn(tags, run_time=0.6))
        self.play(ae.animate.scale(1.04), rate_func=there_and_back, run_time=0.5)
        self.wait(0.8)
