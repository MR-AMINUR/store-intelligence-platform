# Documentation Archive

This directory contains historical documentation files created during development.

## Active Documentation (Keep in Root)

The following files in the project root are the **official documentation**:

### Essential Docs
- **README.md** - Main project documentation
- **DESIGN.md** - Architecture and technical design
- **CHOICES.md** - Design decisions rationale
- **CLI_USAGE.md** - Command-line interface guide
- **PIPELINE_INTEGRATION_GUIDE.md** - CV pipeline integration
- **PIPELINE_QUICK_REFERENCE.md** - Quick CV pipeline reference
- **PYTHON_3.14_UPGRADE_GUIDE.md** - Python 3.14 upgrade instructions
- **QUICK_START_PYTHON_314.md** - Quick setup for Python 3.14
- **PROJECT_READINESS_REPORT.md** - Current project status (95% complete)

## Archived Files

The `archive/` directory contains 40+ historical files:
- Development summaries
- Status checklists
- Fix documentation
- Deployment guides (superseded)
- Validation reports

These files served their purpose during development but are now **obsolete**.

## Cleanup Rationale

During development, many documentation files were created for tracking progress, documenting fixes, and recording decisions. While valuable at the time, they:

1. **Create confusion** - Multiple overlapping guides
2. **Outdated information** - Superseded by newer docs
3. **Clutter root directory** - Harder to find current docs
4. **Redundant content** - Information consolidated elsewhere

## If You Need Historical Info

Check the `archive/` directory for:
- Deployment troubleshooting history
- Frontend-backend connection fixes
- Dataset validation reports
- Task completion checklists
- Old deployment guides

## Current Documentation Strategy

**For Users**:
- Start with `README.md`
- Reference `QUICK_START_PYTHON_314.md` for setup
- Check `PROJECT_READINESS_REPORT.md` for status

**For Developers**:
- Read `DESIGN.md` for architecture
- Review `CHOICES.md` for design rationale
- Use `CLI_USAGE.md` for command reference
- Follow `PIPELINE_INTEGRATION_GUIDE.md` for CV pipeline

**For Deployment**:
- Backend: Already deployed to Render
- Frontend: See `vercel.json` configuration
- Docker: Use `docker-compose.yml`

---

**Last Cleanup**: 2026-05-30  
**Files Archived**: 40  
**Active Docs**: 9
