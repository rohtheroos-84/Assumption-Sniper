import Layout from '../components/Layout'
import IdeaInput from '../components/IdeaInput'
import RunProgress from '../components/RunProgress'

export default function Home() {
  return (
    <Layout>
      <div className="h-container py-12">
        <h1 className="text-3xl font-bold mb-6">assumption sniper — try an idea</h1>
        <IdeaInput />
        <div className="mt-8">
          <RunProgress />
        </div>
      </div>
    </Layout>
  )
}
