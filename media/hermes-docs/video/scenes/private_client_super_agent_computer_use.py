"""Hermes-Agent Private Client Super-Agent Computer_Use documentary explainer.

Narrative arc
-------------
1. Origin — joint work on æ.store
2. Mesh — bounded sovereign private client mesh
3. Runtime — Victus superagent / gauntlet
4. Control — native Windows desktop + VS Installer
5. Loop — glocal industrial agentic engineering

No MathTex used because this Windows host does not have LaTeX installed.
"""
from __future__ import annotations

from manim import *

BG = "#050505"
GOLD = "#D4AF37"
GOLD_DIM = "#7a6524"
INK = "#F0ECE4"
GRID = "#0f0f0f"
MONO = "Menlo"


class Scene0_Origin(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("æ:// storefront", font_size=52, color=GOLD, font=MONO, weight=BOLD)
        subtitle = Text("the exact start of the mesh", font_size=26, color=INK, font=MONO)
        subtitle.next_to(title, DOWN, buff=0.4)
        group = VGroup(title, subtitle)
        group.move_to(ORIGIN)

        self.play(Write(title), run_time=1.5, rate_func=smooth)
        self.wait(0.8)
        self.play(FadeIn(subtitle, shift=UP * 0.25), run_time=1.0)
        self.wait(2.0)

        tag = Text("#opensourceware #250", font_size=22, color=GOLD_DIM, font=MONO)
        tag.to_edge(DOWN)
        self.play(FadeIn(tag, shift=UP * 0.2), run_time=0.7)
        self.wait(1.4)
        self.play(FadeOut(VGroup(title, subtitle, tag)), run_time=0.6)


class Scene1_Mesh(Scene):
    def construct(self):
        self.camera.background_color = BG
        node_alpha = Dot(color=GOLD)
        node_beta = Dot(color=GOLD_DIM)
        node_gamma = Dot(color=GOLD_DIM)
        node_alpha.move_to(LEFT * 4 + UP * 1)
        node_beta.move_to(LEFT * 1.2 + DOWN * 2.2)
        node_gamma.move_to(RIGHT * 2.8 + UP * 1.4)

        label_a = Text("Victus", font_size=24, color=INK, font=MONO).next_to(node_alpha, UP, buff=0.3)
        label_b = Text("Bridge 7860", font_size=24, color=INK, font=MONO).next_to(node_beta, DOWN, buff=0.3)
        label_c = Text("Viewport 5173", font_size=24, color=INK, font=MONO).next_to(node_gamma, UP, buff=0.3)

        edges = VGroup(
            Line(node_alpha, node_beta, stroke_color=GOLD_DIM, stroke_width=2, stroke_opacity=0.7),
            Line(node_beta, node_gamma, stroke_color=GOLD_DIM, stroke_width=2, stroke_opacity=0.7),
            DashedLine(node_alpha, node_gamma, stroke_color=GOLD_DIM, stroke_width=1.5, stroke_opacity=0.35),
        )

        title = Text("pc://mesh/victus/local", font_size=40, color=GOLD, font=MONO, weight=BOLD)
        title.to_edge(UP)
        self.add(title)

        self.play(
            Create(edges, lag_ratio=0.2, run_time=1.6),
            FadeIn(VGroup(node_alpha, node_beta, node_gamma), lag_ratio=0.15, run_time=1.2),
            FadeIn(VGroup(label_a, label_b, label_c), lag_ratio=0.1, run_time=1.2),
            rate_func=smooth,
        )
        self.wait(1.4)

        mesh_text = Text("bounded sovereign private client mesh", font_size=22, color=INK, font=MONO)
        mesh_text.next_to(edges, DOWN, buff=0.5)
        self.play(Write(mesh_text), run_time=1.4)
        self.wait(2.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class Scene2_Runtime(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("VictusSuperagent runtime", font_size=38, color=GOLD, font=MONO, weight=BOLD)
        self.play(Write(title), run_time=1.2)
        self.wait(0.5)

        items = VGroup(
            Text("VictusSuperagent", font_size=26, color=GOLD, font=MONO),
            Text("MachineVitals", font_size=26, color=GOLD_DIM, font=MONO),
            Text("TaskKind / Task history", font_size=26, color=GOLD_DIM, font=MONO),
            Text("gauntlet()", font_size=26, color=GOLD_DIM, font=MONO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)

        self.play(FadeOut(title, shift=UP * 0.3), run_time=0.5)
        self.play(FadeIn(items, lag_ratio=0.12, shift=RIGHT * 0.25), run_time=1.6)
        self.wait(1.4)

        current = VGroup(items[0]).copy().next_to(items, UP * 1.1, aligned_edge=LEFT)
        current.set_color(GOLD)
        self.play(Transform(items[0], current), run_time=0.6)
        self.wait(0.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.4)


class Scene3_Control(Scene):
    def construct(self):
        self.camera.background_color = BG
        title = Text("native computer_use", font_size=40, color=GOLD, font=MONO, weight=BOLD)
        self.play(Write(title), run_time=1.0)
        self.wait(0.5)

        evidence = VGroup(
            Text("WindowsDesktop.enumerate()", font_size=24, color=INK, font=MONO),
            Text("focus(title)", font_size=24, color=INK, font=MONO),
            Text("type_text(text)", font_size=24, color=INK, font=MONO),
            Text("SendInput / user32", font_size=24, color=GOLD_DIM, font=MONO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)

        self.play(FadeOut(title, shift=UP * 0.3), run_time=0.4)
        self.play(FadeIn(evidence, lag_ratio=0.12, shift=RIGHT * 0.25), run_time=1.4)
        self.wait(1.6)

        vs = VGroup(
            Text("VSInstaller.list_installed()", font_size=24, color=GOLD, font=MONO),
            Text("run_installer(...)", font_size=24, color=GOLD_DIM, font=MONO),
            Text("layout export", font_size=24, color=GOLD_DIM, font=MONO),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
        vs.move_to(evidence, aligned_edge=RIGHT).shift(RIGHT * 3.2 + UP * 0.1)

        self.play(FadeIn(vs, shift=UP * 0.25, lag_ratio=0.1), run_time=1.0)
        self.wait(1.8)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class Scene4_Loop(Scene):
    def construct(self):
        self.camera.background_color = BG
        a = Text("+æ://", font_size=72, color=GOLD, font=MONO, weight=BOLD)
        b = Text("computer://", font_size=56, color=GOLD_DIM, font=MONO, weight=BOLD)
        c = Text("pc://", font_size=56, color=GOLD_DIM, font=MONO, weight=BOLD)

        a.to_edge(UP, buff=1.6)
        b.next_to(a, DOWN * 2.2, aligned_edge=LEFT)
        c.next_to(b, DOWN * 1.2, aligned_edge=LEFT)

        arrow1 = Arrow(a.get_bottom() + DOWN * 0.1, b.get_top() + UP * 0.1, stroke_color=GOLD_DIM, stroke_width=2)
        arrow2 = Arrow(b.get_bottom() + DOWN * 0.1, c.get_top() + UP * 0.1, stroke_color=GOLD_DIM, stroke_width=2)

        g = VGroup(a, b, c, arrow1, arrow2)
        g.move_to(ORIGIN)

        self.play(FadeIn(g, lag_ratio=0.2), run_time=1.8)
        self.wait(1.8)

        loop = Text("glocal industrial agentic engineering", font_size=30, color=INK, font=MONO)
        loop.to_edge(DOWN)
        self.play(Write(loop), run_time=1.4)
        self.wait(2.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.6)


class Scene5_EndCard(Scene):
    def construct(self):
        self.camera.background_color = BG
        line = Line(LEFT * 6, RIGHT * 6, stroke_color=GOLD_DIM, stroke_width=1.5)
        line.shift(UP * 0.25)

        end_title = Text("HERMES-AGENT", font_size=64, color=GOLD, font=MONO, weight=BOLD)
        end_sub = Text("Private Client · Super-Agent · Computer_Use", font_size=26, color=INK, font=MONO)
        end_sub.next_to(end_title, DOWN, buff=0.5)
        end_tag = Text("#hermiphicationisinevitable", font_size=22, color=GOLD_DIM, font=MONO)
        end_tag.next_to(end_sub, DOWN, buff=0.45)

        end_group = VGroup(end_title, end_sub, end_tag)
        end_group.move_to(ORIGIN)

        self.play(Create(line), run_time=0.9)
        self.play(Write(end_title), run_time=1.4)
        self.play(FadeIn(end_sub, shift=UP * 0.2), run_time=0.9)
        self.play(FadeIn(end_tag, shift=UP * 0.15), run_time=0.8)
        self.wait(3.0)
        self.play(FadeOut(VGroup(line, *end_group)), run_time=0.8)


SCENES = [
    Scene0_Origin,
    Scene1_Mesh,
    Scene2_Runtime,
    Scene3_Control,
    Scene4_Loop,
    Scene5_EndCard,
]
