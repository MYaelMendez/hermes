use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Surface {
    pub kind: String,
    pub address: String,
    pub target: Option<String>,
    pub active: Option<bool>,
    pub scheme: Option<String>,
}

impl Surface {
    pub fn new(kind: impl Into<String>, address: impl Into<String>) -> Self {
        Surface {
            kind: kind.into(),
            address: address.into(),
            target: None,
            active: None,
            scheme: None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Scheme {
    C,
    LLC,
    Hermes,
    Nous,
    Daollc,
    PC,
    A,
}

impl Scheme {
    pub fn detect(raw: &str) -> Option<Scheme> {
        match raw {
            _ if raw.starts_with("c://") => Some(Scheme::C),
            _ if raw.starts_with("llc://") => Some(Scheme::LLC),
            _ if raw.starts_with("hermes://") => Some(Scheme::Hermes),
            _ if raw.starts_with("H://") => Some(Scheme::Hermes),
            _ if raw.starts_with("NOUS://") => Some(Scheme::Nous),
            _ if raw.starts_with("daollc://") => Some(Scheme::Daollc),
            _ if raw.starts_with("+æ://") => Some(Scheme::A),
            _ if raw.starts_with("pc://") => Some(Scheme::PC),
            _ => None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct HermesConductor {
    pub context: Option<Surface>,
}

impl HermesConductor {
    pub fn new() -> Self {
        HermesConductor { context: None }
    }

    /// Dispatch a single Hermes operator grammar command.
    pub fn dispatch(&mut self, raw: &str) -> Result<Surface, String> {
        let raw = raw.trim();
        if raw.is_empty() {
            return Err("missing cmd".into());
        }

        let scheme = Scheme::detect(raw);

        // c://cc <target>
        if raw.starts_with("c://cc") {
            let target = raw.split_once(' ').map(|(_, t)| t.trim()).unwrap_or("pc://");
            let kind = if target.starts_with("pc://") {
                "private_client"
            } else if target.starts_with("daollc://")
                || target.starts_with("+æ://")
                || target.starts_with("H://")
                || target.starts_with("hermes://")
                || target.starts_with("llc://")
                || target.starts_with("NOUS://")
            {
                "cctx"
            } else {
                "cctx"
            };

            let active = match (kind, target) {
                ("private_client", _) => true,
                ("cctx", t) if !t.is_empty() && !t.eq_ignore_ascii_case("c://") => true,
                _ => false,
            };

            let surface = Surface {
                kind: kind.into(),
                address: target.into(),
                target: Some(target.into()),
                active: Some(active),
                scheme: Some("c".into()),
            };

            self.context = Some(surface.clone());
            return Ok(surface);
        }

        // Primitive surfaces
        match scheme {
            Some(Scheme::LLC) => Ok(Surface {
                kind: "business".into(),
                address: raw.into(),
                target: None,
                active: Some(true),
                scheme: Some("llc".into()),
            }),
            Some(Scheme::Hermes) | Some(Scheme::Nous) => Ok(Surface {
                kind: "runtime".into(),
                address: raw.into(),
                target: None,
                active: Some(true),
                scheme: Some(raw.split_once("://").map(|(s, _)| s).unwrap_or("hermes").into()),
            }),
            Some(Scheme::Daollc) | Some(Scheme::A) => Ok(Surface {
                kind: "dao".into(),
                address: raw.into(),
                target: None,
                active: Some(true),
                scheme: Some(raw.split_once("://").map(|(s, _)| s).unwrap_or("dao").into()),
            }),
            Some(Scheme::PC) => Ok(Surface {
                kind: "private_client".into(),
                address: raw.into(),
                target: None,
                active: Some(true),
                scheme: Some("pc".into()),
            }),
            Some(Scheme::C) => Err(format!("unsupported scheme on its own: {}", raw)),
            None => Err(format!("unsupported scheme: {}", raw)),
        }
    }

    /// Simple text representation suitable for rendering.
    pub fn describe(&self, surface: &Surface) -> String {
        match surface.kind.as_str() {
            "private_client" => format!("{}:private client runtime", surface.address),
            "business" => format!("{}:cli.llc business surface", surface.address),
            "runtime" => format!("{}:hermes-agent runtime", surface.address),
            "dao" => format!(
                "{}:DAO identity context",
                surface
                    .scheme
                    .as_ref()
                    .expect("scheme must be set for dao")
            ),
            "cctx" => {
                let target = surface.target.as_deref().unwrap_or("pc://");
                format!("cctx → {}", target)
            }
            other => format!("{}:unknown({})", surface.address, other),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_business_surface() {
        let mut c = HermesConductor::new();
        let s = c.dispatch("llc://").unwrap();
        assert_eq!(s.kind, "business");
        assert_eq!(s.address, "llc://");
    }

    #[test]
    fn test_runtime_surface() {
        let mut c = HermesConductor::new();
        let s = c.dispatch("hermes://").unwrap();
        assert_eq!(s.kind, "runtime");
        assert_eq!(s.scheme.as_deref(), Some("hermes"));

        let s = c.dispatch("H://").unwrap();
        assert_eq!(s.kind, "runtime");
        assert_eq!(s.scheme.as_deref(), Some("H"));

        let s = c.dispatch("NOUS://").unwrap();
        assert_eq!(s.kind, "runtime");
        assert_eq!(s.scheme.as_deref(), Some("NOUS"));
    }

    #[test]
    fn test_dao_surface() {
        let mut c = HermesConductor::new();
        let s = c.dispatch("daollc://").unwrap();
        assert_eq!(s.kind, "dao");
        assert_eq!(s.scheme.as_deref(), Some("daollc"));

        let s = c.dispatch("+æ://private client^glocal").unwrap();
        assert_eq!(s.kind, "dao");
        assert_eq!(s.scheme.as_deref(), Some("+æ"));
    }

    #[test]
    fn test_private_client_surface() {
        let mut c = HermesConductor::new();
        let s = c.dispatch("pc://").unwrap();
        assert_eq!(s.kind, "private_client");
        assert_eq!(s.scheme.as_deref(), Some("pc"));
    }

    #[test]
    fn test_change_context() {
        let mut c = HermesConductor::new();
        let s = c.dispatch("c://cc pc://").unwrap();
        assert_eq!(s.kind, "private_client");
        assert_eq!(s.active, Some(true));
        assert_eq!(s.target.as_deref(), Some("pc://"));
    }

    #[test]
    fn test_unsupported_scheme() {
        let mut c = HermesConductor::new();
        assert!(c.dispatch("unknown://").is_err());
        assert!(c.dispatch("").is_err());
    }
}
