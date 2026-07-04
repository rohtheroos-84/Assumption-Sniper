import Layout from '../components/Layout'
import IdeaInput from '../components/IdeaInput'
import RunProgress from '../components/RunProgress'
import FeedbackWidget from '../components/FeedbackWidget'

export default function AppPage() {
  return (
    <Layout>
      <div className="h-container py-12">
        <h1 className="text-3xl font-bold mb-2">Run an idea</h1>
        <p className="text-gray-400 text-sm mb-6">Paste a hypothesis. We decompose, critique, simulate, and score it.</p>
        <IdeaInput />
        <div className="mt-8">
          <RunProgress />
        </div>
      </div>
      <FeedbackWidget />
    </Layout>
  )
}
