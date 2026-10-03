//! Feature plan resolution and needs bitmask computation.

use crate::error::TsxError;
use crate::intermediates::Needs;
use crate::registry::{self, ProfileMask, FEATURES};

pub struct FeaturePlan {
    pub indices: Vec<usize>,
    pub names: Vec<&'static str>,
    pub needs: Needs,
}

impl FeaturePlan {
    /// Build a feature execution plan from profile or explicit feature list.
    pub fn build<S: AsRef<str>>(
        profile: Option<&str>,
        features: Option<&[S]>,
    ) -> Result<Self, TsxError> {
        let mut indices = Vec::new();
        let mut names = Vec::new();
        let mut needs = Needs::empty();

        if let Some(req_features) = features {
            for req in req_features {
                let s = req.as_ref();
                if let Some(idx) = registry::find_feature(s) {
                    let def = &FEATURES[idx];
                    indices.push(idx);
                    names.push(def.name);
                    needs |= def.needs;
                } else {
                    return Err(TsxError::UnknownFeature {
                        name: s.to_string(),
                    });
                }
            }
        } else {
            let prof = profile.unwrap_or("core33");
            match prof {
                "minimal" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::MINIMAL) {
                            indices.push(idx);
                            names.push(def.name);
                            needs |= def.needs;
                        }
                    }
                }
                "core33" => {
                    let max_core = 33.min(FEATURES.len());
                    for idx in 0..max_core {
                        let def = &FEATURES[idx];
                        indices.push(idx);
                        names.push(def.name);
                        needs |= def.needs;
                    }
                }
                "extended" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::EXTENDED) {
                            indices.push(idx);
                            names.push(def.name);
                            needs |= def.needs;
                        }
                    }
                }
                "full" => {
                    for (idx, def) in FEATURES.iter().enumerate() {
                        if def.profiles.contains(ProfileMask::FULL) {
                            indices.push(idx);
                            names.push(def.name);
                            needs |= def.needs;
                        }
                    }
                }
                _ => {
                    return Err(TsxError::UnknownProfile {
                        profile: prof.to_string(),
                    });
                }
            }
        }

        Ok(Self {
            indices,
            names,
            needs,
        })
    }

    #[inline]
    pub fn n_features(&self) -> usize {
        self.indices.len()
    }
}
